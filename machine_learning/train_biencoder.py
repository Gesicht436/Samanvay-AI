from pathlib import Path
from typing import Any


def _split_pairs(records: list[dict[str, Any]], test_size: float = 0.15, seed: int = 42) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if len(records) < 2:
        raise ValueError("bi-encoder training requires at least two records for a held-out split")
    import random

    grouped: dict[str, list[int]] = {}
    for index, record in enumerate(records):
        canonical_id = str(record.get("canonical_id", "")).strip()
        if not canonical_id:
            raise ValueError(f"record {index} is missing canonical_id for a leakage-safe split")
        grouped.setdefault(canonical_id, []).append(index)
    if len(grouped) < 2:
        raise ValueError("bi-encoder training requires at least two distinct canonical_id values")

    canonical_ids = list(grouped)
    random.Random(seed).shuffle(canonical_ids)
    heldout_count = min(len(canonical_ids) - 1, max(1, round(len(canonical_ids) * test_size)))
    heldout_ids = set(canonical_ids[:heldout_count])
    training = [record for record in records if str(record["canonical_id"]).strip() not in heldout_ids]
    heldout = [record for record in records if str(record["canonical_id"]).strip() in heldout_ids]
    return training, heldout


def _retrieval_data(records: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, str], dict[str, set[str]]]:
    queries: dict[str, str] = {}
    corpus: dict[str, str] = {}
    relevant_docs: dict[str, set[str]] = {}
    for index, record in enumerate(records):
        query_id = f"query-{index}"
        document_id = str(record.get("canonical_id") or f"document-{index}")
        queries[query_id] = str(record["anchor"])
        corpus[document_id] = str(record["positive"])
        relevant_docs[query_id] = {document_id}
    return queries, corpus, relevant_docs


def _print_retrieval_metrics(model: Any, records: list[dict[str, Any]]) -> dict[str, float]:
    import numpy as np

    queries, corpus, relevant_docs = _retrieval_data(records)
    corpus_ids = list(corpus)
    query_vectors = model.encode(list(queries.values()), normalize_embeddings=True)
    corpus_vectors = model.encode([corpus[document_id] for document_id in corpus_ids], normalize_embeddings=True)
    cosine_scores = np.asarray(query_vectors) @ np.asarray(corpus_vectors).T
    recalls = {1: 0, 5: 0, 10: 0}
    reciprocal_rank = 0.0
    query_ids = list(queries)
    for row_index, query_id in enumerate(query_ids):
        ranking = np.argsort(-cosine_scores[row_index])
        relevant = relevant_docs[query_id]
        for cutoff in recalls:
            recalls[cutoff] += int(any(corpus_ids[int(index)] in relevant for index in ranking[:cutoff]))
        for rank, corpus_index in enumerate(ranking[:10], start=1):
            if corpus_ids[int(corpus_index)] in relevant:
                reciprocal_rank += 1 / rank
                break
    count = max(1, len(query_ids))
    metrics = {f"Recall@{cutoff}": value / count for cutoff, value in recalls.items()}
    metrics["MRR@10"] = reciprocal_rank / count
    print(
        "Held-out retrieval: "
        + ", ".join(f"{name}={value:.4f}" for name, value in metrics.items())
    )
    return metrics


def train(output_dir: str | Path = "machine_learning/model_weights/bge_m3_cpes", train_file: str | Path = "data/ml_training/biencoder_pairs.jsonl") -> dict[str, float]:
    """Fine-tune BGE-M3 using an explicit held-out retrieval split."""
    from datasets import load_dataset
    from sentence_transformers import (
        SentenceTransformer,
        SentenceTransformerTrainer,
        SentenceTransformerTrainingArguments,
    )
    from sentence_transformers.evaluation import InformationRetrievalEvaluator
    from sentence_transformers.losses import MultipleNegativesRankingLoss, TripletLoss

    model = SentenceTransformer("BAAI/bge-m3")
    loaded = load_dataset("json", data_files=str(train_file), split="train")
    records = loaded.to_list()
    training_records, heldout_records = _split_pairs(records)
    has_negative = any(record.get("negative") for record in records)
    if has_negative and any(not record.get("negative") for record in training_records):
        negative_rows = [record for record in training_records if record.get("negative")]
        positive_rows = [record for record in training_records if not record.get("negative")]
    else:
        negative_rows = training_records if has_negative else []
        positive_rows = [] if has_negative else training_records

    queries, corpus, relevant_docs = _retrieval_data(heldout_records)
    evaluator = InformationRetrievalEvaluator(
        queries=queries,
        corpus=corpus,
        relevant_docs=relevant_docs,
        precision_recall_at_k=[1, 5, 10],
        mrr_at_k=[10],
        ndcg_at_k=[],
        map_at_k=[],
        name="heldout",
    )
    args = SentenceTransformerTrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=3,
        per_device_train_batch_size=32,
        warmup_steps=100,
        report_to=[],
    )

    def run_trainer(rows: list[dict[str, Any]], triplet: bool) -> None:
        if not rows:
            return
        from datasets import Dataset

        columns = {"sentence_0": [str(row["anchor"]) for row in rows], "sentence_1": [str(row["positive"]) for row in rows]}
        if triplet:
            columns["sentence_2"] = [str(row["negative"]) for row in rows]
            loss = TripletLoss(model)
        else:
            loss = MultipleNegativesRankingLoss(model)
        trainer = SentenceTransformerTrainer(
            model=model,
            args=args,
            train_dataset=Dataset.from_dict(columns),
            loss=loss,
        )
        trainer.train()

    run_trainer(positive_rows, triplet=False)
    run_trainer(negative_rows, triplet=True)
    evaluator(model)
    metrics = _print_retrieval_metrics(model, heldout_records)
    model.save(str(output_dir))
    return metrics
