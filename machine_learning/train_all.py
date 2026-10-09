import argparse
import time
from collections.abc import Callable
from typing import Any


def run_stages(stages: list[str]) -> list[tuple[str, str, str, float]]:
    from machine_learning.reranker.train import train as train_reranker
    from machine_learning.train_biencoder import train as train_biencoder
    from machine_learning.train_ner import train_ner

    stage_functions: dict[str, tuple[Callable[[], Any], str]] = {
        "ner": (train_ner, "machine_learning/model_weights/ner_deberta"),
        "biencoder": (train_biencoder, "machine_learning/model_weights/bge_m3_cpes"),
        "reranker": (train_reranker, "machine_learning/model_weights/reranker.xgb"),
    }
    unknown = set(stages) - set(stage_functions)
    if unknown:
        raise ValueError(f"unknown training stage(s): {', '.join(sorted(unknown))}")

    results: list[tuple[str, str, str, float]] = []
    for stage in ("ner", "biencoder", "reranker"):
        if stage not in stages:
            continue
        train_function, model_path = stage_functions[stage]
        started = time.perf_counter()
        metric = train_function()
        elapsed = time.perf_counter() - started
        if isinstance(metric, dict):
            metric_text = ", ".join(f"{key}={value:.4f}" for key, value in metric.items())
        else:
            metric_name = {"ner": "macro F1", "reranker": "validation AUC"}[stage]
            metric_text = f"{metric_name}={float(metric or 0.0):.4f}"
        results.append((stage, model_path, metric_text, elapsed))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Samanvay-AI models in dependency order")
    parser.add_argument("--stage", default="ner,biencoder,reranker", help="comma-separated stage names")
    arguments = parser.parse_args()
    stages = [stage.strip() for stage in arguments.stage.split(",") if stage.strip()]
    results = run_stages(stages)

    print(f"{'Stage':<12} {'Model path':<55} {'Metric':<45} {'Training time (s)':>17}")
    print("-" * 132)
    for stage, model_path, metric, elapsed in results:
        print(f"{stage:<12} {model_path:<55} {metric:<45} {elapsed:>17.2f}")


if __name__ == "__main__":
    main()
