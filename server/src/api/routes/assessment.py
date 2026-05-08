# File: server/src/api/routes/assessment.py  # Full file path comment as requested

from typing import Any, Dict  # Import typing helpers for authenticated user dependency payload.
from fastapi import APIRouter, Depends, HTTPException, Query, status  # Import FastAPI router, dependency injection, query validation, and HTTP tools.
from src.core.config import settings  # Import application settings for API prefix configuration.
from src.core.dependencies import search_user  # Import JWT-based current-user dependency for protected routes.
from src.schemas.assessment import PHQ9AssessmentHistoryResponse, PHQ9AssessmentRequest, PHQ9AssessmentResponse  # Import PHQ-9 request, response, and history schemas.
from src.services.assessment_service import get_phq9_history, run_phq9_assessment_and_save  # Import PHQ-9 service functions for scoring, saving, and history retrieval.
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

@router.get("/phq9/history", response_model=PHQ9AssessmentHistoryResponse, status_code=status.HTTP_200_OK)  # Define protected endpoint for paginated PHQ-9 history retrieval.
async def see_phq9_history(  # Define async route handler for PHQ-9 history requests.
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of PHQ-9 history records to return"),  # Validate page size in the route before service logic runs.
    skip: int = Query(default=0, ge=0, description="Number of PHQ-9 history records to skip"),  # Validate pagination offset in the route before service logic runs.
    user: Dict[str, Any] = Depends(search_user),  # Inject authenticated user context from JWT dependency.
) -> PHQ9AssessmentHistoryResponse:  # Return typed PHQ-9 history response payload.
    user_id = user.get("_id")  # Read authenticated user identifier from dependency output.
    if not isinstance(user_id, str) or not user_id.strip():  # Validate authenticated context before calling service logic.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token")  # Return 401 when token context is malformed.

    try:  # Start protected execution block for PHQ-9 history service call.
        history_items = await get_phq9_history(user_id=user_id, limit=limit, skip=skip)  # Fetch paginated PHQ-9 history from MongoDB.
        return PHQ9AssessmentHistoryResponse(count=len(history_items), limit=limit, skip=skip, items=history_items)  # Wrap items with pagination metadata for frontend use.
    except HTTPException:  # Re-raise explicit HTTP exceptions unchanged when present.
        raise  # Preserve status code and detail from known API/service-level errors.
    except Exception:  # Catch any unexpected runtime errors from service or database processing.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch PHQ-9 assessment history")  # Return safe generic 500 response.
