from fastapi import APIRouter

router = APIRouter()


@router.get("/spare-locator")
def spare_locator(canonical_id: str, requesting_cpse: str, minimum_idle_days: int = 30):
    return {"canonical_id": canonical_id, "requesting_cpse": requesting_cpse, "minimum_idle_days": minimum_idle_days, "items": []}


@router.get("/visualize")
def visualize(canonical_id: str):
    return {"nodes": [], "edges": [], "canonical_id": canonical_id}
