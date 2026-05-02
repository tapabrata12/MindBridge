from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from src.core.dependencies import search_user
from src.core.config import settings
from src.schemas.assessment import PHQ9AssessmentRequest, PHQ9AssessmentResponse
from src.services.assessment_service import run_phq9_assessment

router = APIRouter(prefix=f"{settings.PREFIX}/assessment", tags=["Assessment"])

@router.post("/phq9", response_model=PHQ9AssessmentResponse, status_code=status.HTTP_200_OK)
async def phq9_assessment(
    assessment: PHQ9AssessmentRequest,
    user: Dict[str, Any] = Depends(search_user),
) -> PHQ9AssessmentResponse:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login to start Assessment")

    user_id = user.get("_id")
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(  # Raise explicit HTTP error when auth context is invalid.
            status_code=status.HTTP_401_UNAUTHORIZED,  # Use 401 because identity/session context is not valid.
            detail="Invalid user token",  # Return clear and safe error message to client.
        )  # End 401 exception.

    try:
        answer = await run_phq9_assessment(assessment)
        return answer
    except HTTPException:  # If a known HTTP exception appears, keep it unchanged.
        raise  # Re-raise so status code and message are preserved exactly.
    except Exception as exc:  # Catch unexpected runtime failures as a safe fallback.
        raise HTTPException(  # Convert unknown server errors into a stable API response format.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Use 500 for unexpected backend failure.
            detail=f"Failed to process PHQ-9 assessment: {str(exc)}",  # Include concise debug hint in error detail.
        )  # End 500 exception.
