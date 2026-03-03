from fastapi import APIRouter
from src.schemas.screening_schema import PHQ9Request,PHQ9Response
from src.services.screening_service import calculate_phq9_score
from src.core.config import settings
router_screening = APIRouter(tags=["Screening"],prefix=settings.API_PREFIX)

@router_screening.post("/screening/phq9",response_model=PHQ9Response)
def phq9(req: PHQ9Request):
    res = calculate_phq9_score(req.answers)
    return res
