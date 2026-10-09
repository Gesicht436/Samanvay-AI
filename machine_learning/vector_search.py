from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid4, uuid5

from backend.app.config import get_settings
from backend.app.contracts.matching import CandidateMatch
from machine_learning.active_learning import get_active_learning_queue
from machine_learning.safety import safety_violations
from machine_learning.subvectors import DOMAINS, encode_subvectors, subvector_texts
from machine_learning.tiers import assign_tier


class VectorSearcher:
    def __init__(self, client: Any = None, encoder: Any = None) -> None:
        self.settings = get_settings()
        self.client = client
        self.encoder = encoder

    def get_candidate_skus(
        self,
        raw_description: str,
        top_k: int = 10,
        *,
        reranker: Any = None,
        item_type: str | None = None,
    ) -> list[CandidateMatch]:
        if self.client is None:
            raise RuntimeError("Vector search is unavailable because the Qdrant client is not configured")
        if self.encoder is None:
            raise RuntimeError("Vector search is unavailable because the embedding model is not loaded")
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        from machine_learning.ner_tagger import extract_attributes

        query_attributes = extract_attributes(raw_description).model_dump()
        query_vectors = encode_subvectors(query_attributes, self.encoder)
        qdrant_filter = None
        requested_type = item_type or query_attributes.get("item_type")
        if requested_type:
            from qdrant_client.models import FieldCondition, Filter, MatchAny

            canonical_types = {
                "FLANGE": ["FLANGE", "FLANGE_WELD_NECK", "FLANGE_SLIP_ON", "FLANGE_BLIND"],
                "VALVE": ["VALVE", "GATE_VALVE", "BALL_VALVE", "GLOBE_VALVE"],
                "GATE_VALVE": ["GATE_VALVE"],
                "BALL_VALVE": ["BALL_VALVE"],
                "BOLT": ["BOLT", "STUD_BOLT"],
                "STUD_BOLT": ["STUD_BOLT"],
            }
            accepted_types = canonical_types.get(str(requested_type).upper(), [requested_type])
            qdrant_filter = Filter(
                must=[FieldCondition(key="item_type", match=MatchAny(any=accepted_types))]
            )
        limit = top_k * 5 if reranker is not None else top_k
        hits_by_id: dict[str, dict[str, Any]] = {}
        for domain in DOMAINS:
            if not hasattr(self.client, "query_points"):
                raise RuntimeError(
                    "Qdrant client must support query_points for named-vector search"
                )
            response = self.client.query_points(
                collection_name=self.settings.qdrant_collection,
                query=query_vectors[domain],
                using=domain,
                limit=limit,
                query_filter=qdrant_filter,
            )
            hits = response.points
            for hit in hits:
                hit_key = str(hit.payload["canonical_id"])
                candidate = hits_by_id.setdefault(
                    hit_key,
                    {"payload": hit.payload, "scores": {}},
                )
                candidate["scores"][domain] = float(hit.score)
        payload_keys = (
            "item_type",
            "size_nb_mm",
            "pressure_class",
            "metallurgy",
            "facing_end",
            "standard",
            "canonical_description",
            "indian_standard",
            "oisd_standard",
            "eil_specification",
            "gem_category",
            "gem_bid_number",
            "cppp_tender_id",
            "mesc_code",
            "manufacturer",
            "product_form",
            "coating",
            "inspection_class",
            "document_number",
            "project",
            "end_connection",
            "temperature_rating",
            "purchase_order",
            "certificate_number",
            "bid_number",
            "inspection_agency",
        )
        candidates: list[tuple[float, CandidateMatch]] = []
        for candidate_data in hits_by_id.values():
            hit_payload = candidate_data["payload"]
            score_values = list(candidate_data["scores"].values())
            mean_score = sum(score_values) / len(DOMAINS)
            cosine = max(score_values) * 0.75 + mean_score * 0.25
            if cosine < 0.70:
                continue
            candidate_attributes = {key: hit_payload.get(key) for key in payload_keys}
            violations = safety_violations(query_attributes, candidate_attributes)
            domain_scores = {
                domain: float(candidate_data["scores"].get(domain, 0.0))
                for domain in DOMAINS
            }
            score = (
                cosine
                if reranker is None
                else float(reranker.score(query_attributes, candidate_attributes, cosine, domain_scores))
            )
            tier = assign_tier(score, violations)
            reasons: list[str] = []
            if reranker is not None:
                model = getattr(reranker, "model", None)
                if model is not None:
                    from machine_learning.explain import explain

                    reasons = explain(
                        query_attributes,
                        {**candidate_attributes, "cosine": cosine, "domain_scores": domain_scores},
                        model,
                    )
                else:
                    reasons = [f"Compatibility reranker score: {score:.2f}"]
            match = CandidateMatch(
                canonical_id=str(hit_payload["canonical_id"]),
                similarity=score,
                tier=tier,
                violations=violations,
                reasons=reasons,
                domain_scores=domain_scores,
                **candidate_attributes,
            )
            if tier.value != "Tier-1":
                get_active_learning_queue().observe(raw_description, match, cosine=cosine)
            candidates.append((score, match))
        if reranker is None:
            return [match for _, match in candidates]
        candidates.sort(key=lambda item: item[0], reverse=True)
        return [match for _, match in candidates[:top_k]]


def index_canonical_master(csv_path: str | Path, client: Any, encoder: Any) -> int:
    import polars as pl
    from qdrant_client.models import (
        CreateAlias,
        CreateAliasOperation,
        DeleteAlias,
        DeleteAliasOperation,
        Distance,
        PointStruct,
        VectorParams,
    )

    settings = get_settings()
    frame = pl.read_csv(csv_path)
    collection_alias = settings.qdrant_collection
    staging_collection = f"{collection_alias}__staging_{uuid4().hex}"
    while client.collection_exists(staging_collection):
        staging_collection = f"{collection_alias}__staging_{uuid4().hex}"
    rows = frame.to_dicts()
    domain_texts = {domain: [] for domain in DOMAINS}
    for row in rows:
        for domain, text in subvector_texts(row).items():
            domain_texts[domain].append(text)
    domain_vectors = {
        domain: encoder.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=True,
        )
        for domain, texts in domain_texts.items()
    }
    domain_vectors = {
        domain: values.tolist() if hasattr(values, "tolist") else values
        for domain, values in domain_vectors.items()
    }
    points = []
    for row_index, row in enumerate(rows):
        vectors = {
            domain: [float(component) for component in domain_vectors[domain][row_index]]
            for domain in DOMAINS
        }
        point_id = str(uuid5(NAMESPACE_URL, str(row["canonical_id"])))
        points.append(PointStruct(id=point_id, vector=vectors, payload=row))
    client.create_collection(
        staging_collection,
        vectors_config={
            domain: VectorParams(size=1024, distance=Distance.COSINE)
            for domain in DOMAINS
        },
    )
    client.upsert(staging_collection, points=points)

    aliases = client.get_aliases().aliases
    current_alias = next(
        (alias for alias in aliases if alias.alias_name == collection_alias),
        None,
    )
    alias_operations = []
    if current_alias is not None:
        alias_operations.append(
            DeleteAliasOperation(delete_alias=DeleteAlias(alias_name=collection_alias))
        )
    elif client.collection_exists(collection_alias):
        client.delete_collection(collection_alias)
    alias_operations.append(
        CreateAliasOperation(
            create_alias=CreateAlias(
                collection_name=staging_collection,
                alias_name=collection_alias,
            )
        )
    )
    client.update_collection_aliases(alias_operations)
    return len(points)
