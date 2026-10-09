from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.api.deps import get_vector_searcher
from backend.app.contracts.matching import CandidateMatch, MatchResult
from backend.app.matching.tolerance import classify_candidate
from machine_learning.active_learning import ActiveLearningBootstrapper, get_active_learning_queue
from machine_learning.ner_tagger import extract_attributes

router = APIRouter()


class MatchRequest(BaseModel):
    raw_description: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=50)
    rerank: bool = True


class HITLResolveRequest(BaseModel):
    item_id: str
    accepted: bool
    corrected_candidate: str | None = Field(default=None, min_length=1)


class HITLBootstrapItem(BaseModel):
    query: str = Field(min_length=1)
    candidate: CandidateMatch
    cosine: float | None = Field(default=None, ge=0.0, le=1.0)


class HITLBootstrapRequest(BaseModel):
    items: list[HITLBootstrapItem]


@router.post("", response_model=MatchResult | None)
def match_item(request: MatchRequest, searcher=Depends(get_vector_searcher)):
    attributes = extract_attributes(request.raw_description)
    reranker = None
    if request.rerank:
        from machine_learning.reranker import CompatibilityRanker

        reranker = CompatibilityRanker()
    try:
        candidates = searcher.get_candidate_skus(
            request.raw_description,
            top_k=request.top_k,
            reranker=reranker,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not candidates:
        return None
    result = classify_candidate(attributes, candidates[0])
    result.matches = candidates
    return result


@router.get("/hitl-queue")
def hitl_queue():
    return {"items": get_active_learning_queue().list_items()}


@router.get("/hitl-training-examples")
def hitl_training_examples():
    return {"items": get_active_learning_queue().training_examples()}


@router.post("/hitl-bootstrap")
def bootstrap_hitl_queue(payload: HITLBootstrapRequest):
    records = [item.model_dump() for item in payload.items]
    count = ActiveLearningBootstrapper(get_active_learning_queue()).bootstrap(records)
    return {"status": "bootstrapped", "items_added": count}


@router.post("/hitl-resolve")
def resolve_hitl(payload: HITLResolveRequest):
    result = get_active_learning_queue().resolve(
        payload.item_id,
        accepted=payload.accepted,
        corrected_candidate=payload.corrected_candidate,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="HITL review item was not found or already resolved.")
    return {"status": "recorded", "training_example": result}
