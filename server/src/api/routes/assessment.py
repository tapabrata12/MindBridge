# File: server/src/api/routes/assessment.py  # Full file path comment as requested

from typing import Annotated, Any, Dict  # Import Annotated for modern dependency typing and Dict/Any for user payload typing.
from fastapi import APIRouter, Depends, HTTPException, status  # Import FastAPI routing, dependency, error, and status tools.
from src.core.config import settings  # Import app settings so API prefix stays centralized.
from src.core.dependencies import search_user  # Import JWT auth dependency to protect this route.
from src.schemas.assessment import PHQ9AssessmentRequest, PHQ9AssessmentResponse  # Import validated request/response schemas.
from src.services.assessment_service import run_phq9_assessment  # Import PHQ-9 scoring service entrypoint.

router = APIRouter(prefix=f"{settings.PREFIX}/assessment", tags=["Assessment"])  # Register assessment router at /api/assessment.

AuthenticatedUser = Annotated[Dict[str, Any], Depends(search_user)]  # Create reusable dependency alias for authenticated user context.

@router.post("/phq9", response_model=PHQ9AssessmentResponse, status_code=status.HTTP_200_OK)  # Define protected POST endpoint for PHQ-9 submission.
async def submit_phq9_assessment(  # Define async route handler for PHQ-9 scoring requests.
    payload: PHQ9AssessmentRequest,  # Receive validated PHQ-9 payload from request body.
    user: AuthenticatedUser,  # Inject authenticated user via JWT dependency.
) -> PHQ9AssessmentResponse:  # Return strongly typed PHQ-9 response model.
    user_id = user.get("_id")  # Read user id from dependency output as a defensive auth-context check.
    if not isinstance(user_id, str) or not user_id.strip():  # Validate user id shape before proceeding.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token")  # Return 401 when token context is malformed.

    result = await run_phq9_assessment(request_data=payload)  # Call async service layer to compute PHQ-9 scoring output.
    if not isinstance(result, PHQ9AssessmentResponse):  # Defensively ensure service contract stays correct if future refactors happen.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process PHQ-9 assessment")  # Return safe generic 500 if contract breaks unexpectedly.

    return result  # Return validated PHQ-9 assessment response.