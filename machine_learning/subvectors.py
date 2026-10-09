"""Create domain-specific embeddings for dimensions, materials, ratings, and standards."""

from collections.abc import Mapping
from typing import Any

DOMAINS = ("dim", "met", "pt", "std")
_DOMAIN_FIELDS = {
    "dim": ("size_nb_mm", "size_inch", "dn_code", "dimension", "schedule", "end_connection"),
    "met": ("metallurgy", "material_grade", "coating", "product_form"),
    "pt": ("pressure_class", "temperature_rating", "pressure_rating"),
    "std": (
        "standard",
        "indian_standard",
        "oisd_standard",
        "eil_specification",
        "gem_category",
        "gem_bid_number",
        "cppp_tender_id",
        "mesc_code",
    ),
}


def _attributes(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, str):
        from machine_learning.ner_tagger import _regex_attributes

        return _regex_attributes(value).model_dump()
    raise TypeError("subvector input must be a mapping, material attributes, or description")


def subvector_texts(value: Any) -> dict[str, str]:
    attributes = _attributes(value)
    description = str(attributes.get("canonical_description") or attributes.get("raw_description") or "").strip()
    texts: dict[str, str] = {}
    for domain, fields in _DOMAIN_FIELDS.items():
        values = [
            f"{field.replace('_', ' ')}: {attributes[field]}"
            for field in fields
            if attributes.get(field) is not None and str(attributes[field]).strip()
        ]
        texts[domain] = "; ".join(values) if values else description
    if not any(texts.values()):
        raise ValueError("subvector input has neither domain attributes nor a description")
    return texts


def encode_subvectors(value: Any, encoder: Any) -> dict[str, list[float]]:
    vectors: dict[str, list[float]] = {}
    for domain, text in subvector_texts(value).items():
        encoded = encoder.encode(text, normalize_embeddings=True)
        encoded = encoded.tolist() if hasattr(encoded, "tolist") else encoded
        if encoded and isinstance(encoded[0], list):
            encoded = encoded[0]
        vectors[domain] = [float(component) for component in encoded]
    return vectors
