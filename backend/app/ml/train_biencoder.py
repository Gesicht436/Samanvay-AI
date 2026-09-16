"""
Fine-tuning BAAI/bge-m3 Bi-Encoder on 8,000 CPSE Contrastive Pairs.
Uses MultipleNegativesRankingLoss (MNRL) with CUDA FP16 mixed precision on RTX 3060.
Saves fine-tuned checkpoint to backend/app/ml/model_weights/bge_m3_cpes/
"""

import os
import json
import logging
import torch
from pathlib import Path
from torch.utils.data import DataLoader
from sentence_transformers import SentenceTransformer, InputExample, losses
from backend.app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = settings.DATA_DIR / "ml_training" / "biencoder_pairs.jsonl"
OUTPUT_DIR = settings.BGE_M3_MODEL_PATH


def _load_pairs(filepath: Path):
    """Loads contrastive pairs from a JSONL file. Returns list of (anchor, positive) tuples."""
    pairs = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            pairs.append((data["anchor"], data["positive"]))
    return pairs


def train_biencoder(epochs: int = 3, batch_size: int = 16, lr: float = 2e-5):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"[+] Initializing BGE-M3 training on device: {device} (CUDA: {torch.cuda.is_available()})")
    if device == "cuda":
        logger.info(f"[+] GPU: {torch.cuda.get_device_name(0)}")

    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing training dataset at {DATA_FILE}")

    # Load contrastive pairs and split train/dev (90/10)
    logger.info(f"[+] Loading contrastive pairs from {DATA_FILE}...")
    all_pairs = _load_pairs(DATA_FILE)
    split_idx = max(1, int(len(all_pairs) * 0.9))
    train_pairs = all_pairs[:split_idx]
    dev_pairs   = all_pairs[split_idx:]
    logger.info(f"[+] Loaded {len(all_pairs)} pairs (train={len(train_pairs)}, dev={len(dev_pairs)})")

    train_examples = [InputExample(texts=[a, p]) for a, p in train_pairs]

    model = SentenceTransformer(settings.BASE_BGE_M3, device=device)
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
    train_loss = losses.MultipleNegativesRankingLoss(model)

    warmup_steps = int(len(train_dataloader) * epochs * 0.1)
    logger.info(f"[+] Starting training for {epochs} epochs (warmup: {warmup_steps} steps, batch_size: {batch_size})...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build cosine similarity evaluator on the held-out dev set.
    # sentence_transformers will run this after each epoch and print the score.
    # The best checkpoint (highest cosine similarity on dev) is saved automatically.
    evaluator = None
    if dev_pairs:
        from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
        anchors   = [a for a, _ in dev_pairs]
        positives = [p for _, p in dev_pairs]
        # All dev pairs are positive (label=1.0)
        labels    = [1.0] * len(dev_pairs)
        evaluator = EmbeddingSimilarityEvaluator(
            sentences1=anchors,
            sentences2=positives,
            scores=labels,
            name="dev_cosine",
            show_progress_bar=False
        )
        logger.info(f"[+] EmbeddingSimilarityEvaluator configured on {len(dev_pairs)} dev pairs.")

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        warmup_steps=warmup_steps,
        optimizer_params={"lr": lr},
        weight_decay=0.01,
        show_progress_bar=True,
        use_amp=(device == "cuda"),  # Automatic Mixed Precision for RTX 3060
        evaluator=evaluator,
        evaluation_steps=len(train_dataloader),  # evaluate at end of each epoch
        output_path=str(OUTPUT_DIR),             # saves best checkpoint here
    )

    logger.info(f"[+] Saving fine-tuned BGE-M3 model weights to {OUTPUT_DIR}...")
    model.save(str(OUTPUT_DIR))
    logger.info("[+] Fine-tuning complete and weights persisted successfully!")



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=16)
    args = parser.parse_args()

    train_biencoder(epochs=args.epochs, batch_size=args.batch_size)
