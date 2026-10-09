from machine_learning.train_ner import LABEL_TO_ID, _bio_labels, _eval_strategy_argument


def test_bio_alignment_marks_beginning_and_inside_tokens():
    offsets = [(0, 4), (5, 9), (10, 15)]
    entities = [{"start": 5, "end": 15, "label": "SIZE"}]

    labels = _bio_labels(offsets, entities)

    assert labels == [
        LABEL_TO_ID["O"],
        LABEL_TO_ID["B-SIZE"],
        LABEL_TO_ID["I-SIZE"],
    ]


def test_eval_strategy_name_tracks_transformers_signature():
    class NewArguments:
        def __init__(self, eval_strategy="no"):
            pass

    class OldArguments:
        def __init__(self, evaluation_strategy="no"):
            pass

    assert _eval_strategy_argument(NewArguments) == "eval_strategy"
    assert _eval_strategy_argument(OldArguments) == "evaluation_strategy"
