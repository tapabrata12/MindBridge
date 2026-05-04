# File: server/src/api/routes/assessment.py  # Full file path comment as requested

from typing import Any, Dict  # Import typing helpers for authenticated user dependency payload.
from fastapi import APIRouter, Depends, HTTPException, status  # Import FastAPI router, dependency injection, and HTTP error/status tools.
from src.core.config import settings  # Import application settings for API prefix configuration.
from src.core.dependencies import search_user  # Import JWT-based current-user dependency for protected routes.
from src.schemas.assessment import PHQ9AssessmentRequest, PHQ9AssessmentResponse  # Import PHQ-9 request and response schemas.
from src.services.assessment_service import run_phq9_assessment_and_save  # Import PHQ-9 service function that computes and persists assessment output.

router = APIRouter(prefix=f"{settings.PREFIX}/assessment", tags=["Assessment"])  # Create assessment router mounted at /api/assessment.

@router.post("/phq9", response_model=PHQ9AssessmentResponse, status_code=status.HTTP_200_OK)  # Define protected endpoint for PHQ-9 scoring submissions.
async def submit_phq9_assessment(  # Define async route handler for PHQ-9 requests.
    payload: PHQ9AssessmentRequest,  # Accept validated PHQ-9 request body.
    user: Dict[str, Any] = Depends(search_user),  # Inject authenticated user context from JWT dependency.
) -> PHQ9AssessmentResponse:  # Return typed PHQ-9 response payload.
    user_id = user.get("_id")  # Read authenticated user identifier from dependency output.
    if not isinstance(user_id, str) or not user_id.strip():  # Validate authenticated context before calling service logic.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token")  # Return 401 when token context is malformed.

    try:  # Start protected execution block for PHQ-9 service call.
        return await run_phq9_assessment_and_save(user_id=user_id, request=payload)  # Compute PHQ-9 result and persist it to MongoDB.
    except HTTPException:  # Re-raise explicit HTTP exceptions unchanged when present.
        raise  # Preserve status code and detail from known API/service-level errors.
    except Exception:  # Catch any unexpected runtime errors from service or database processing.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process PHQ-9 assessment")  # Return safe generic 500 response.