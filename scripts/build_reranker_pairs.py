import argparse
import random
from pathlib import Path
from typing import Any

import numpy as np

from machine_learning.subvectors import DOMAINS, subvector_texts


def build_pairs(
    canonical_csv: str | Path,
    output_parquet: str | Path,
    positives_per_item: int = 5,
    hard_negatives_per_item: int = 15,
    seed: int = 42,
) -> int:
    import polars as pl
    from sentence_transformers import SentenceTransformer

    frame = pl.read_csv(canonical_csv)
    required = {"item_type", "size_nb_mm", "pressure_class", "metallurgy", "canonical_description"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"canonical CSV missing required columns: {', '.join(sorted(missing))}")
    items = frame.to_dicts()
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        groups.setdefault(str(item["item_type"]), []).append(item)

    randomizer = random.Random(seed)
    pairs: list[dict[str, Any]] = []
    for query in items:
        same_type = groups[str(query["item_type"])]
        other_items = [item for item in same_type if item["canonical_description"] != query["canonical_description"]]
        if not other_items:
            other_items = [query]
        positives = [
            item for item in other_items
            if item["size_nb_mm"] == query["size_nb_mm"]
            and item["pressure_class"] == query["pressure_class"]
            and item["metallurgy"] == query["metallurgy"]
        ]
        if not positives:
            positives = [query]
        hard_negatives = [
            item for item in other_items
            if item["size_nb_mm"] != query["size_nb_mm"]
            or item["pressure_class"] != query["pressure_class"]
            or item["metallurgy"] != query["metallurgy"]
        ]
        if not hard_negatives:
            hard_negatives = [
                item for item in items
                if item["canonical_description"] != query["canonical_description"]
                and item["item_type"] != query["item_type"]
            ] or [
                item for item in items if item["canonical_description"] != query["canonical_description"]
            ]
        if not hard_negatives:
            continue
        for label, pool, count in (
            (1, positives, positives_per_item),
            (0, hard_negatives, hard_negatives_per_item),
        ):
            for candidate in randomizer.choices(pool, k=count):
                pairs.append(
                    {
                        "query": query["canonical_description"],
                        "candidate": candidate["canonical_description"],
                        "query_item": query,
                        "candidate_item": candidate,
                        "label": label,
                    }
                )

    encoder = SentenceTransformer("BAAI/bge-m3")
    texts = [pair[key] for pair in pairs for key in ("query", "candidate")]
    vectors = encoder.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True)
    for index, pair in enumerate(pairs):
        query_vector = vectors[index * 2]
        candidate_vector = vectors[index * 2 + 1]
        pair["cosine"] = float(query_vector @ candidate_vector)
    domain_texts = [
        text
        for pair in pairs
        for item_key in ("query_item", "candidate_item")
        for text in (subvector_texts(pair[item_key])[domain] for domain in DOMAINS)
    ]
    domain_vectors = encoder.encode(
        domain_texts,
        normalize_embeddings=True,
        batch_size=64,
        show_progress_bar=True,
    )
    for index, pair in enumerate(pairs):
        pair.pop("query_item")
        pair.pop("candidate_item")
        for domain_index, domain in enumerate(DOMAINS):
            query_vector = domain_vectors[index * len(DOMAINS) * 2 + domain_index]
            candidate_vector = domain_vectors[index * len(DOMAINS) * 2 + len(DOMAINS) + domain_index]
            pair[f"{domain}_cosine"] = float(np.dot(query_vector, candidate_vector))
    destination = Path(output_parquet)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(pairs).select(
        "query",
        "candidate",
        "cosine",
        *(f"{domain}_cosine" for domain in DOMAINS),
        "label",
    ).write_parquet(destination)
    return len(pairs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build cosine-scored reranker training pairs")
    parser.add_argument("--canonical-csv", default="data/taxonomies/canonical_master.csv")
    parser.add_argument("--output", default="data/ml_training/reranker_pairs.parquet")
    parser.add_argument("--seed", type=int, default=42)
    arguments = parser.parse_args()
    count = build_pairs(arguments.canonical_csv, arguments.output, seed=arguments.seed)
    print(f"Wrote {count} pairs to {arguments.output}")


if __name__ == "__main__":
    main()
