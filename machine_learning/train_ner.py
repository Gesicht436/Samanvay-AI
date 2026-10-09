from pathlib import Path
from typing import Any

from machine_learning.ner_tagger import ENTITY_TYPES

LABEL_NAMES = ["O"] + [prefix + "-" + entity for entity in ENTITY_TYPES for prefix in ("B", "I")]
LABEL_TO_ID = {label: index for index, label in enumerate(LABEL_NAMES)}


def _eval_strategy_argument(training_arguments: Any) -> str:
    import inspect

    parameters = inspect.signature(training_arguments).parameters
    return "eval_strategy" if "eval_strategy" in parameters else "evaluation_strategy"


def _bio_labels(offsets: list[tuple[int, int]], entities: list[dict[str, object]]) -> list[int]:
    labels = [LABEL_TO_ID["O"]] * len(offsets)
    for entity in entities:
        start = int(entity["start"])
        end = int(entity["end"])
        label = str(entity["label"])
        matched = [index for index, (token_start, token_end) in enumerate(offsets) if token_end > start and token_start < end]
        for position, token_index in enumerate(matched):
            prefix = "B" if position == 0 else "I"
            labels[token_index] = LABEL_TO_ID[f"{prefix}-{label}"]
    return labels


def _entity_metrics(predictions: Any, references: Any) -> dict[str, float]:
    import numpy as np
    from seqeval.metrics import classification_report

    predicted_ids = np.argmax(predictions, axis=-1)
    true_sequences: list[list[str]] = []
    predicted_sequences: list[list[str]] = []
    for predicted_row, reference_row in zip(predicted_ids, references):
        true_labels: list[str] = []
        predicted_labels: list[str] = []
        for predicted_id, reference_id in zip(predicted_row, reference_row):
            if int(reference_id) == -100:
                continue
            true_labels.append(LABEL_NAMES[int(reference_id)])
            predicted_labels.append(LABEL_NAMES[int(predicted_id)])
        true_sequences.append(true_labels)
        predicted_sequences.append(predicted_labels)

    report = classification_report(true_sequences, predicted_sequences, output_dict=True, zero_division=0)
    entity_f1 = {entity: float(report.get(entity, {}).get("f1-score", 0.0)) for entity in ENTITY_TYPES}
    entity_f1["macro_f1"] = sum(entity_f1.values()) / len(ENTITY_TYPES)
    return entity_f1


def train_ner(
    train_file: str | Path = "data/ml_training/ner_train.jsonl",
    output_dir: str | Path = "machine_learning/model_weights/ner_deberta",
) -> float:
    """Fine-tune DeBERTa with character-offset BIO alignment."""
    from datasets import load_dataset
    from transformers import (
        AutoModelForTokenClassification,
        AutoTokenizer,
        DataCollatorForTokenClassification,
        Trainer,
        TrainerCallback,
        TrainingArguments,
    )

    model_name = "microsoft/deberta-v3-small"
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        model = AutoModelForTokenClassification.from_pretrained(model_name, num_labels=len(LABEL_NAMES), id2label=dict(enumerate(LABEL_NAMES)), label2id=LABEL_TO_ID)
    except OSError:
        model_name = "roberta-base"
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        model = AutoModelForTokenClassification.from_pretrained(model_name, num_labels=len(LABEL_NAMES), id2label=dict(enumerate(LABEL_NAMES)), label2id=LABEL_TO_ID)

    dataset = load_dataset("json", data_files=str(train_file), split="train")
    split = dataset.train_test_split(test_size=0.15, seed=42)

    def tokenize_batch(batch: dict[str, list[object]]) -> dict[str, list[object]]:
        encoded = tokenizer(batch["text"], truncation=True, return_offsets_mapping=True)
        encoded["labels"] = [_bio_labels(offsets, entities) for offsets, entities in zip(encoded["offset_mapping"], batch["labels"])]
        encoded.pop("offset_mapping")
        return encoded

    train_dataset = split["train"].map(tokenize_batch, batched=True, remove_columns=dataset.column_names)
    eval_dataset = split["test"].map(tokenize_batch, batched=True, remove_columns=dataset.column_names)
    strategy_key = _eval_strategy_argument(TrainingArguments)
    training_arguments = {
        "output_dir": str(output_dir),
        "num_train_epochs": 3,
        "per_device_train_batch_size": 16,
        "save_strategy": "epoch",
        "logging_steps": 50,
        "report_to": [],
        "load_best_model_at_end": True,
        "metric_for_best_model": "macro_f1",
        "greater_is_better": True,
    }
    training_arguments[strategy_key] = "epoch"
    args = TrainingArguments(**training_arguments)

    class EntityMetricPrinter(TrainerCallback):
        def on_evaluate(self, args: Any, state: Any, control: Any, metrics: dict[str, float], **kwargs: Any) -> None:
            values = ", ".join(f"{entity} F1={metrics.get(f'eval_{entity}', 0.0):.4f}" for entity in ENTITY_TYPES)
            print(f"Epoch {state.epoch}: {values}; macro F1={metrics.get('eval_macro_f1', 0.0):.4f}")

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=DataCollatorForTokenClassification(tokenizer),
        compute_metrics=lambda output: _entity_metrics(output.predictions[0] if isinstance(output.predictions, tuple) else output.predictions, output.label_ids),
        callbacks=[EntityMetricPrinter()],
    )
    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    return float(trainer.state.best_metric or 0.0)
