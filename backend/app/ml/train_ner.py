"""
Fine-tuning DeBERTa-v3 on 5,000 Industrial NER Samples.
Extracts: ITEM_TYPE, SIZE, PRESSURE_RATING, METALLURGY, FACING_END, STANDARD.
Optimized for NVIDIA RTX 3060 Laptop GPU with FP16 mixed precision.
"""

import json
import logging
import torch
from pathlib import Path
from typing import List, Dict, Any
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification
)
from datasets import Dataset
from backend.app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = settings.DATA_DIR / "ml_training" / "ner_train.jsonl"
OUTPUT_DIR = settings.NER_MODEL_PATH

LABELS = [
    "O",
    "B-ITEM_TYPE", "I-ITEM_TYPE",
    "B-SIZE", "I-SIZE",
    "B-PRESSURE_RATING", "I-PRESSURE_RATING",
    "B-METALLURGY", "I-METALLURGY",
    "B-FACING_END", "I-FACING_END",
    "B-STANDARD", "I-STANDARD"
]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for i, l in enumerate(LABELS)}


def convert_annotations_to_bio(text: str, labels: List[Dict[str, Any]], tokenizer) -> Dict[str, Any]:
    """Tokenizes text and aligns character offsets to subword token BIO labels."""
    tokens = tokenizer(
        text,
        return_offsets_mapping=True,
        truncation=True,
        max_length=128
    )
    offset_mapping = tokens["offset_mapping"]
    token_labels = []

    for start_char, end_char in offset_mapping:
        if start_char == end_char:
            token_labels.append(-100) # Special tokens ([CLS], [SEP])
            continue

        assigned = "O"
        for ent in labels:
            e_start = ent["start"]
            e_end = ent["end"]
            e_lbl = ent["label"]

            if start_char >= e_start and end_char <= e_end:
                if start_char == e_start:
                    assigned = f"B-{e_lbl}"
                else:
                    assigned = f"I-{e_lbl}"
                break
        token_labels.append(LABEL2ID.get(assigned, 0))

    tokens["labels"] = token_labels
    return tokens


def train_ner(epochs: int = 3, batch_size: int = 16, lr: float = 3e-5):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"[+] Initializing DeBERTa-v3 NER training on device: {device} (CUDA: {torch.cuda.is_available()})")

    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing dataset at {DATA_FILE}")

    tokenizer = AutoTokenizer.from_pretrained(settings.BASE_DEBERTA)
    model = AutoModelForTokenClassification.from_pretrained(
        settings.BASE_DEBERTA,
        num_labels=len(LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID
    )

    logger.info(f"[+] Loading and tokenizing {DATA_FILE}...")
    processed_samples = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            aligned = convert_annotations_to_bio(item["text"], item["labels"], tokenizer)
            processed_samples.append({
                "input_ids": aligned["input_ids"],
                "attention_mask": aligned["attention_mask"],
                "labels": aligned["labels"]
            })

    # Split train/eval
    split_idx = int(len(processed_samples) * 0.9)
    train_data = Dataset.from_list(processed_samples[:split_idx])
    eval_data = Dataset.from_list(processed_samples[split_idx:])

    logger.info(f"[+] Train samples: {len(train_data)}, Eval samples: {len(eval_data)}")

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=lr,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        fp16=(device == "cuda"),
        logging_steps=50,
        save_total_limit=1,
        load_best_model_at_end=True
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_data,
        eval_dataset=eval_data,
        tokenizer=tokenizer,
        data_collator=DataCollatorForTokenClassification(tokenizer=tokenizer)
    )

    logger.info("[+] Starting DeBERTa-v3 token classification training...")
    trainer.train()

    logger.info(f"[+] Persisting final NER model to {OUTPUT_DIR}...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    logger.info("[+] NER fine-tuning complete!")


if __name__ == "__main__":
    train_ner()
