from fastapi import APIRouter
from src.core.config import settings

router_health = APIRouter(tags=["Health"])


@router_health.get("/")
def health_check():
    return {"status": "Mental Health Backend Running"}