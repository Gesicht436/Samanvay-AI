from machine_learning.train_biencoder import _retrieval_data, _split_pairs


def test_biencoder_split_reserves_heldout_records_deterministically():
    rows = [
        {"anchor": f"query-{index}", "positive": f"canonical-{index}", "canonical_id": str(index)}
        for index in range(20)
    ]

    training, heldout = _split_pairs(rows)

    assert len(heldout) == 3
    assert len(training) == 17
    assert set(map(id, training)).isdisjoint(map(id, heldout))


def test_biencoder_split_keeps_canonical_ids_together():
    rows = [
        {"anchor": f"query-{index}", "positive": f"item-{index}", "canonical_id": f"CAN-{index // 2}"}
        for index in range(20)
    ]

    training, heldout = _split_pairs(rows)

    training_ids = {row["canonical_id"] for row in training}
    heldout_ids = {row["canonical_id"] for row in heldout}
    assert training_ids.isdisjoint(heldout_ids)
    assert len(heldout) == 4


def test_heldout_records_form_information_retrieval_inputs():
    queries, corpus, relevant_docs = _retrieval_data(
        [{"anchor": "query", "positive": "item", "canonical_id": "CAN-1"}]
    )

    assert queries == {"query-0": "query"}
    assert corpus == {"CAN-1": "item"}
    assert relevant_docs == {"query-0": {"CAN-1"}}
