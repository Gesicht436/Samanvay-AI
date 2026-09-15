"""
API V1 Material Code Matching, Deterministic Verification & HITL Triage Routes.
Exposes single-item standardization, candidate retrieval, ASME tolerance verification,
and Batch Human-in-the-Loop triage actions.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from backend.app.api.deps import get_db
from backend.app.ml.ner_tagger import extract_attributes
from backend.app.ml.vector_search import get_candidate_skus
from backend.app.matching.tolerance import evaluate_compatibility, evaluate_candidate_pool
from backend.app.matching.active_learning import active_learning_cache
from backend.app.contracts.material import ExtractedMaterialAttributes
from backend.app.contracts.matching import MatchEvaluationResult, EquivalenceTier
from backend.app.ingestion.storage import save_reconciliation_decision, get_recent_audits
from backend.app.graph.queries import link_reconciled_sku

router = APIRouter(prefix="/match", tags=["Matching & HITL Triage"])


class SingleMatchRequest(BaseModel):
    query: str = Field(..., description="Raw ERP procurement description string", json_schema_extra={"example": "FLG WNRF 4IN 300# A105"})
    top_k: int = Field(default=5, ge=1, le=20)


class HITLResolveRequest(BaseModel):
    source_sku: str
    source_cpse: str
    canonical_id: str
    decision: str = Field(..., description="APPROVE, REJECT, or RECLASSIFY")
    tier: str = Field(default="TIER_1_IDENTICAL")
    confidence: float = Field(default=1.0)
    officer: str = Field(default="MAYANK_ANAND")
    source_description: Optional[str] = None
    action_note: Optional[str] = None


class BulkHITLResolveRequest(BaseModel):
    items: List[HITLResolveRequest]
    officer: str = Field(default="MAYANK_ANAND")


@router.post("/single")
def match_single_item(request: SingleMatchRequest) -> Dict[str, Any]:
    """
    Standardizes a raw procurement string:
    1. Extracts mechanical specifications (Item Type, Size, Pressure, Alloy, Facing).
    2. Retrieves top candidate SKUs from Qdrant vector index (<15ms).
    3. Evaluates all candidates against deterministic ASME B16.5 & ASTM tolerance rules.
    4. Categorizes into Tier-1 (Identical), Tier-2 (Substitute), or Tier-3 (Incompatible).
    5. Applies online Active Learning Dynamic Reranking based on prior engineer decisions.
    """
    source_attrs = extract_attributes(request.query)
    candidates = get_candidate_skus(request.query, top_k=request.top_k)
    evaluated_results = evaluate_candidate_pool(source_attrs, candidates)

    # Online Active Learning dynamic reranker (instant feedback learning without model retraining)
    evaluated_results = active_learning_cache.apply_dynamic_reranking(request.query, None, evaluated_results)

    # Determine recommended primary match
    recommended_match = evaluated_results[0] if evaluated_results else None

    return {
        "query": request.query,
        "extracted_attributes": source_attrs.model_dump(),
        "total_candidates": len(evaluated_results),
        "primary_match": recommended_match.model_dump() if recommended_match else None,
        "candidates": [r.model_dump() for r in evaluated_results]
    }


@router.get("/hitl-queue")
def get_hitl_triage_queue(limit: int = 25) -> List[Dict[str, Any]]:
    """
    Retrieves pending ambiguous matches (70%-90% confidence or Tier-2 upgrades)
    for side-by-side human review in the Next.js HITL Triage Panel.
    """
    # Curated fixtures for demonstration and active review
    queue_items = [
        {
            "queue_id": "HITL-001",
            "source_cpse": "IOCL",
            "source_depot": "Panipat Refinery, Haryana",
            "source_sku": "IOCL-MM-0004128",
            "source_description": "FLG WNRF 4IN 300# A105",
            "suggested_cpse": "ONGC",
            "suggested_depot": "Hazira Gas Processing Plant, Gujarat",
            "suggested_sku": "ONGC-MAT-0000092",
            "suggested_description": "FLANGE WELD NECK 4\" CL300 ASTM A105 RF",
            "canonical_id": "CAN-000009",
            "tier": "TIER_1_IDENTICAL",
            "confidence": 0.96,
            "unit_cost_inr": 12400,
            "available_qty": 45,
            "days_idle": 210,
            "parameters": [
                {"name": "Item Type", "source": "FLANGE_WELD_NECK", "candidate": "FLANGE_WELD_NECK", "status": "EXACT"},
                {"name": "Nominal Bore", "source": "100.0 mm (4\")", "candidate": "100.0 mm (4\")", "status": "EXACT"},
                {"name": "Pressure Class", "source": "Class 300", "candidate": "Class 300", "status": "EXACT"},
                {"name": "Metallurgy", "source": "ASTM A105", "candidate": "ASTM A105", "status": "EXACT"},
                {"name": "Facing", "source": "RF (Raised Face)", "candidate": "RF (Raised Face)", "status": "EXACT"}
            ],
            "rationale": "100% specification parity. Safe identical drop-in replacement across depots."
        },
        {
            "queue_id": "HITL-002",
            "source_cpse": "BPCL",
            "source_depot": "Kochi Refinery, Kerala",
            "source_sku": "BPCL-SAP-0001094",
            "source_description": "VLV-GT-DN50-CL300-WCB-RF",
            "suggested_cpse": "IOCL",
            "suggested_depot": "Mathura Refinery, Uttar Pradesh",
            "suggested_sku": "IOCL-MM-0002190",
            "suggested_description": "VALVE GATE 2\" CLASS 600 ASTM A216 WCB RF",
            "canonical_id": "CAN-001198",
            "tier": "TIER_2_SUBSTITUTE",
            "confidence": 0.88,
            "unit_cost_inr": 48500,
            "available_qty": 18,
            "days_idle": 320,
            "parameters": [
                {"name": "Item Type", "source": "GATE_VALVE", "candidate": "GATE_VALVE", "status": "EXACT"},
                {"name": "Nominal Bore", "source": "50.0 mm (2\")", "candidate": "50.0 mm (2\")", "status": "EXACT"},
                {"name": "Pressure Class", "source": "Class 300", "candidate": "Class 600", "status": "UPGRADE"},
                {"name": "Metallurgy", "source": "ASTM A216 WCB", "candidate": "ASTM A216 WCB", "status": "EXACT"},
                {"name": "Facing", "source": "RF", "candidate": "RF", "status": "EXACT"}
            ],
            "rationale": "Valid functional upgrade: Class 600 valve exceeds required Class 300 pressure rating."
        },
        {
            "queue_id": "HITL-003",
            "source_cpse": "ONGC",
            "source_depot": "Uran Plant, Maharashtra",
            "source_sku": "ONGC-MAT-0005512",
            "source_description": "FLANGE BLIND 6\" 300# A105 RF",
            "suggested_cpse": "BPCL",
            "suggested_depot": "Mumbai Refinery, Mahul, Maharashtra",
            "suggested_sku": "BPCL-SAP-0003310",
            "suggested_description": "FLG-BLD-DN150-CL300-SS316-RF",
            "canonical_id": "CAN-000591",
            "tier": "TIER_2_SUBSTITUTE",
            "confidence": 0.85,
            "unit_cost_inr": 34000,
            "available_qty": 26,
            "days_idle": 195,
            "parameters": [
                {"name": "Item Type", "source": "FLANGE_BLIND", "candidate": "FLANGE_BLIND", "status": "EXACT"},
                {"name": "Nominal Bore", "source": "150.0 mm (6\")", "candidate": "150.0 mm (6\")", "status": "EXACT"},
                {"name": "Pressure Class", "source": "Class 300", "candidate": "Class 300", "status": "EXACT"},
                {"name": "Metallurgy", "source": "ASTM A105", "candidate": "ASTM A182 F316", "status": "UPGRADE"},
                {"name": "Facing", "source": "RF", "candidate": "RF", "status": "EXACT"}
            ],
            "rationale": "Safe metallurgical upgrade: Stainless SS316 offers superior corrosion resistance over Carbon Steel A105."
        }
    ]
    return queue_items[:limit]


@router.post("/hitl-resolve")
def resolve_hitl_item(
    request: HITLResolveRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Handles single-item Human-in-the-Loop decision:
    - Persists audit log to PostgreSQL.
    - Writes reconciled MAPS_TO relationship to Neo4j.
    """
    verified = (request.decision.upper() == "APPROVE")

    audit = save_reconciliation_decision(
        db=db,
        source_sku=request.source_sku,
        source_cpse=request.source_cpse,
        matched_canonical_id=request.canonical_id,
        tier=request.tier,
        confidence=request.confidence,
        verified_by_hitl=verified,
        hitl_officer=request.officer,
        source_description=request.source_description,
        action_note=request.action_note or f"Action: {request.decision}"
    )

    if verified:
        link_reconciled_sku(
            sku_code=request.source_sku,
            cpse=request.source_cpse,
            canonical_id=request.canonical_id,
            tier=request.tier,
            confidence=request.confidence,
            verified_by_hitl=True,
            officer=request.officer
        )

    # Record feedback into Active Learning Cache for online dynamic reranking
    active_learning_cache.record_feedback(
        source_description=request.source_description or request.source_sku,
        source_sku=request.source_sku,
        canonical_id=request.canonical_id,
        decision=request.decision,
        officer=request.officer,
        action_note=request.action_note or f"Action: {request.decision}"
    )

    return {
        "status": "SUCCESS",
        "decision": request.decision,
        "audit_id": audit.id,
        "message": f"Successfully recorded decision '{request.decision}' for SKU {request.source_sku}."
    }


@router.post("/hitl-bulk-resolve")
def bulk_resolve_hitl_items(
    request: BulkHITLResolveRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Batch Triage Mode: 1-click bulk approval of multiple safe verified matches.
    """
    approved_count = 0
    for item in request.items:
        save_reconciliation_decision(
            db=db,
            source_sku=item.source_sku,
            source_cpse=item.source_cpse,
            matched_canonical_id=item.canonical_id,
            tier=item.tier,
            confidence=item.confidence,
            verified_by_hitl=True,
            hitl_officer=request.officer,
            action_note="Bulk Approved via Batch Triage Mode"
        )
        link_reconciled_sku(
            sku_code=item.source_sku,
            cpse=item.source_cpse,
            canonical_id=item.canonical_id,
            tier=item.tier,
            confidence=item.confidence,
            verified_by_hitl=True,
            officer=request.officer
        )
        # Record into Active Learning Cache
        active_learning_cache.record_feedback(
            source_description=item.source_description or item.source_sku,
            source_sku=item.source_sku,
            canonical_id=item.canonical_id,
            decision=item.decision,
            officer=request.officer,
            action_note="Bulk Approved via Batch Triage Mode"
        )
        approved_count += 1

    return {
        "status": "SUCCESS",
        "approved_count": approved_count,
        "message": f"Successfully bulk-approved {approved_count} safe material matches."
    }


@router.get("/feedback-cache")
def get_feedback_cache() -> Dict[str, Any]:
    """
    Retrieves active learning feedback cache statistics and historical records
    powering online dynamic candidate reranking without retraining.
    """
    return {
        "stats": active_learning_cache.get_stats(),
        "records": active_learning_cache.get_all_records(),
    }
