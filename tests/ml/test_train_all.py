import importlib

from machine_learning.train_all import run_stages


def test_selected_training_stages_run_in_dependency_order(monkeypatch):
    calls = []
    ner = importlib.import_module("machine_learning.train_ner")
    biencoder = importlib.import_module("machine_learning.train_biencoder")
    reranker = importlib.import_module("machine_learning.reranker.train")
    monkeypatch.setattr(ner, "train_ner", lambda: calls.append("ner") or 0.9)
    monkeypatch.setattr(biencoder, "train", lambda: calls.append("biencoder") or {"MRR@10": 0.8})
    monkeypatch.setattr(reranker, "train", lambda: calls.append("reranker") or 0.85)

    results = run_stages(["reranker", "biencoder", "ner"])

    assert calls == ["ner", "biencoder", "reranker"]
    assert [result[0] for result in results] == ["ner", "biencoder", "reranker"]
