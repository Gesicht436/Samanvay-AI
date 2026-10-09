from machine_learning.subvectors import DOMAINS, encode_subvectors, subvector_texts


class FakeEncoder:
    def encode(self, text, normalize_embeddings=True):
        return [float(len(text)), 1.0]


def test_four_domain_decomposition_assigns_attributes_to_expected_subvectors():
    texts = subvector_texts(
        {
            "size_nb_mm": 100,
            "end_connection": "FLANGED",
            "metallurgy": "SS316",
            "pressure_class": 300,
            "temperature_rating": 120,
            "indian_standard": "IS 1239",
            "standard": "ASME B16.5",
        }
    )

    assert set(texts) == {"dim", "met", "pt", "std"}
    assert "100" in texts["dim"] and "FLANGED" in texts["dim"]
    assert "SS316" in texts["met"]
    assert "300" in texts["pt"] and "120" in texts["pt"]
    assert "IS 1239" in texts["std"] and "ASME B16.5" in texts["std"]


def test_encoder_returns_four_consistent_vectors():
    vectors = encode_subvectors({"size_nb_mm": 100}, FakeEncoder())

    assert tuple(vectors) == DOMAINS
    assert all(vector == [float(len(vector_text)), 1.0] for vector, vector_text in zip(vectors.values(), subvector_texts({"size_nb_mm": 100}).values()))
