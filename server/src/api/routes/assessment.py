# File: server/src/api/routes/assessment.py  # Full file path comment as requested

from typing import Any, Dict  # Import typing helpers for authenticated user dependency payload.
from fastapi import APIRouter, Depends, HTTPException, Query, status  # Import FastAPI router, dependency injection, query validation, and HTTP tools.
from typer.cli import state

from src.core.config import settings  # Import application settings for API prefix configuration.
from src.core.dependencies import search_user  # Import JWT-based current-user dependency for protected routes.
from src.schemas.assessment import PHQ9AssessmentHistoryResponse, PHQ9AssessmentRequest, PHQ9AssessmentResponse  # Import PHQ-9 request, response, and history schemas.
from src.services.assessment_service import get_phq9_history, run_phq9_assessment_and_save  # Import PHQ-9 service functions for scoring, saving, and history retrieval.
from src.graph.assessment_graph import start_conversation, continue_conversation
from src.schemas.assessment import PHQ9ConversationStartRequest,PHQ9ConversationContinueRequest,PHQ9ConversationResponse

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


@router.post("/phq9/start", response_model=PHQ9ConversationResponse, status_code=status.HTTP_200_OK)
async def start_phq9_conversation(payload: PHQ9ConversationStartRequest, user: Dict[str, Any]= Depends(search_user)):
    user_id = user.get("_id")  # Read authenticated user identifier from dependency output.
    if not isinstance(user_id,str) or not user_id.strip():  # Validate authenticated context before calling service logic.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid user token")  # Return 401 when token context is malformed.

    try:
        state = await start_conversation(payload.notes)

        return PHQ9ConversationResponse(
            answers= state.get("answers", []),
            assistant_message= state.get("assistant_message"),
            score_options= state.get('score_options'),
            current_question_id= state.get("current_question_id"),
            is_complete= state.get("is_complete"),
            needs_answer= state.get("needs_answer"),
            crisis_support= state.get("crisis_support"),
            result= state.get("result"),
            Error= state.get("Error")
        )

    except HTTPException:  # If an HTTPException was already raised somewhere inside, let it pass through unchanged
        raise  # Re-raise it exactly as-is — same pattern as your existing routes
    except Exception:  # Catch any other unexpected crash (graph error, MongoDB issue, anything)
        raise HTTPException(  # Convert it to a clean HTTP error instead of a raw Python traceback
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # 500 means "something broke on our server"
            detail="Failed to start PHQ-9 conversation"
            # Safe generic message — never expose raw error internals to clients
        )


@router.post("/phq9/continue", response_model=PHQ9ConversationResponse, status_code=status.HTTP_200_OK)
async def continue_phq9_conversation(payload: PHQ9ConversationContinueRequest, user: Dict[str,Any] = Depends(search_user)):
    user_id = user.get("_id")  # Read authenticated user identifier from dependency output.

    if not isinstance(user_id,str) or not user_id.strip():  # Validate authenticated context before calling service logic.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid user token")  # Return 401 when token context is malformed.

    try:
        answer_from_user =  [data.model_dump() for data in payload.answers]
        state = await continue_conversation(answers=answer_from_user, notes=payload.notes, incoming_score=payload.incoming_score)

        if state.get("is_complete"):
            completed_answers_schema = PHQ9AssessmentRequest(answers=state.get("answers", []), notes=payload.notes)
            await run_phq9_assessment_and_save(user_id, completed_answers_schema)

        return PHQ9ConversationResponse(
            assistant_message= state.get("assistant_message"),
            score_options= state.get("score_options"),
            current_question_id= state.get("current_question_id"),
            answers= state.get("answers",[]),
            is_complete= state.get("is_complete",False),
            needs_answer= state.get("needs_answer", False),
            result= state.get("result"),
            crisis_support=state.get("crisis_support"),
            Error= state.get("Error")
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(  # Convert it to a clean HTTP error instead of a raw Python traceback
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # 500 means "something broke on our server"
            detail="Failed to continue PHQ-9 conversation"
            # Safe generic message — never expose raw error internals to clients
        )
