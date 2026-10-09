from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
def current_user():
    return {"user_id": "anonymous", "role": "reviewer"}
