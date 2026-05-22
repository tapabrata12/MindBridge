# File: server/src/api/routes/assessment.py  # Mark the exact file path for this route file.

from typing import Any, Dict, List, Literal, Optional  # Import typing helpers for request, response, and auth payload shapes.

from fastapi import APIRouter, Depends, HTTPException, Query, status  # Import FastAPI tools for routes, auth dependencies, errors, and status codes.
from pydantic import BaseModel, ConfigDict, Field, field_validator  # Import Pydantic v2 tools for request and response validation.

from src.core.config import settings  # Import application settings for the API prefix.
from src.core.dependencies import search_user  # Import JWT-based current-user dependency for protected routes.
from src.graph.assessment_graph import continue_phq9_conversation, start_phq9_conversation  # Import the LangGraph PHQ-9 conversation helpers.
from src.schemas.assessment import PHQ9AnswerValue, PHQ9AssessmentHistoryResponse, PHQ9AssessmentRequest, PHQ9AssessmentResponse, PHQ9AssessmentResult, PHQ9CrisisSupport, PHQ9QuestionAnswer  # Import PHQ-9 schemas.
from src.services.assessment_service import get_phq9_history, run_phq9_assessment_and_save  # Import assessment DB/service functions.


router = APIRouter(prefix=f"{settings.PREFIX}/assessment", tags=["Assessment"])  # Create assessment router mounted at /api/assessment.


class PHQ9ConversationStartRequest(BaseModel):  # Define the request body for starting a PHQ-9 conversation.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)  # Reject unknown fields and trim string whitespace.
    notes: Optional[str] = Field(default=None, min_length=1, max_length=1000, description="Optional note to save when the PHQ-9 is completed")  # Allow optional notes.


class PHQ9ConversationAnswerRequest(BaseModel):  # Define the request body for one PHQ-9 conversation answer.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)  # Reject unknown fields and trim string whitespace.
    answers: List[PHQ9QuestionAnswer] = Field(default_factory=list, max_length=8, description="Answers already collected before this turn")  # Store previous answers only.
    score: PHQ9AnswerValue = Field(..., description="The new answer score for the current question")  # Store the newest answer score.
    notes: Optional[str] = Field(default=None, min_length=1, max_length=1000, description="Optional note to save when the PHQ-9 is completed")  # Carry optional notes through the flow.

    @field_validator("answers")  # Run validation on the previous answers list.
    @classmethod  # Mark this as a class-level validator.
    def validate_answer_sequence(cls, values: List[PHQ9QuestionAnswer]) -> List[PHQ9QuestionAnswer]:  # Ensure answers are in simple order.
        expected_ids = list(range(1, len(values) + 1))  # Build the expected sequence: 1, 2, 3, and so on.
        actual_ids = [answer.question_id for answer in values]  # Read the actual question IDs from the payload.
        if actual_ids != expected_ids:  # Check that the frontend did not skip or reorder questions.
            raise ValueError("answers must be in order starting from question_id 1")  # Return a clear validation message.
        return values  # Return validated answers unchanged.


class PHQ9ConversationResponse(BaseModel):  # Define the response shape for both conversation endpoints.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)  # Keep response output strict and clean.
    assessment_type: Literal["phq9"] = Field(default="phq9", description="Assessment type identifier")  # Mark the response as PHQ-9.
    answers: List[PHQ9QuestionAnswer] = Field(default_factory=list, description="Answers collected so far")  # Return answers for the frontend to send next time.
    current_question_id: Optional[int] = Field(default=None, ge=1, le=9, description="Current PHQ-9 question number")  # Return active question number.
    assistant_message: str = Field(..., min_length=1, description="Message or question to show the user")  # Return chat-style text.
    score_options: Dict[int, str] = Field(default_factory=dict, description="Allowed PHQ-9 score options")  # Return labels for score buttons.
    is_complete: bool = Field(..., description="Whether all 9 PHQ-9 answers are complete")  # Tell frontend if flow ended.
    needs_answer: bool = Field(..., description="Whether frontend should ask for another score")  # Tell frontend if another answer is needed.
    result: Optional[PHQ9AssessmentResult] = Field(default=None, description="Final PHQ-9 result when complete")  # Return final scoring result.
    crisis_support: Optional[PHQ9CrisisSupport] = Field(default=None, description="Crisis support when item 9 is positive")  # Return crisis resources when needed.
    error: Optional[str] = Field(default=None, description="Validation error message when present")  # Return safe validation errors.


def _get_authenticated_user_id(user: Dict[str, Any]) -> str:  # Create helper to safely read the user ID from JWT dependency output.
    user_id = user.get("_id")  # Read authenticated user ID from the dependency result.
    if not isinstance(user_id, str) or not user_id.strip():  # Validate that the ID exists and is a non-empty string.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token")  # Reject malformed auth context.
    return user_id  # Return the safe user ID.


def _build_conversation_response(graph_state: Dict[str, Any]) -> PHQ9ConversationResponse:  # Convert LangGraph state into API response model.
    return PHQ9ConversationResponse(  # Build a validated response object.
        assessment_type="phq9",  # Mark this response as PHQ-9.
        answers=graph_state.get("answers", []),  # Return collected answers.
        current_question_id=graph_state.get("current_question_id"),  # Return current question number if present.
        assistant_message=graph_state.get("assistant_message", "PHQ-9 conversation ready."),  # Return graph message safely.
        score_options=graph_state.get("score_options", {}),  # Return score labels.
        is_complete=graph_state.get("is_complete", False),  # Return completion flag.
        needs_answer=graph_state.get("needs_answer", True),  # Return whether frontend needs another score.
        result=graph_state.get("result"),  # Return final result when present.
        crisis_support=graph_state.get("crisis_support"),  # Return crisis resources when present.
        error=graph_state.get("error"),  # Return validation error when present.
    )  # Finish response construction.


@router.post("/phq9", response_model=PHQ9AssessmentResponse, status_code=status.HTTP_200_OK)  # Keep existing full PHQ-9 submit endpoint.
async def submit_phq9_assessment(  # Define async route handler for full PHQ-9 requests.
    payload: PHQ9AssessmentRequest,  # Accept complete PHQ-9 request body.
    user: Dict[str, Any] = Depends(search_user),  # Require authenticated access token.
) -> PHQ9AssessmentResponse:  # Return typed PHQ-9 response.
    user_id = _get_authenticated_user_id(user)  # Read and validate authenticated user ID.
    try:  # Start protected service call.
        return await run_phq9_assessment_and_save(user_id=user_id, request=payload)  # Score and save complete PHQ-9.
    except HTTPException:  # Preserve known HTTP errors.
        raise  # Re-raise known HTTP errors unchanged.
    except Exception:  # Catch unexpected errors.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process PHQ-9 assessment")  # Return safe generic 500.


@router.post("/phq9/conversation/start", response_model=PHQ9ConversationResponse, status_code=status.HTTP_200_OK)  # Add endpoint to start chat-style PHQ-9.
async def start_phq9_conversation_route(  # Define async route handler for starting the conversation.
    payload: PHQ9ConversationStartRequest,  # Accept optional notes in request body.
    user: Dict[str, Any] = Depends(search_user),  # Require authenticated access token.
) -> PHQ9ConversationResponse:  # Return first PHQ-9 conversation question.
    _get_authenticated_user_id(user)  # Validate auth even though no DB write happens yet.
    try:  # Start protected graph call.
        graph_state = await start_phq9_conversation(notes=payload.notes)  # Ask LangGraph for question 1.
        return _build_conversation_response(dict(graph_state))  # Convert graph state into API response.
    except HTTPException:  # Preserve known HTTP errors.
        raise  # Re-raise known HTTP errors unchanged.
    except Exception:  # Catch unexpected graph errors.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to start PHQ-9 conversation")  # Return safe generic 500.


@router.post("/phq9/conversation/answer", response_model=PHQ9ConversationResponse, status_code=status.HTTP_200_OK)  # Add endpoint to submit one PHQ-9 answer.
async def answer_phq9_conversation_route(  # Define async route handler for one conversation turn.
    payload: PHQ9ConversationAnswerRequest,  # Accept previous answers plus the newest score.
    user: Dict[str, Any] = Depends(search_user),  # Require authenticated access token.
) -> PHQ9ConversationResponse:  # Return next question or final result.
    user_id = _get_authenticated_user_id(user)  # Read and validate authenticated user ID.
    try:  # Start protected graph and save flow.
        previous_answers = [answer.model_dump() for answer in payload.answers]  # Convert Pydantic answers into plain dictionaries for LangGraph.
        graph_state = await continue_phq9_conversation(answers=previous_answers, incoming_score=payload.score, notes=payload.notes)  # Run one LangGraph turn.

        if graph_state.get("is_complete"):  # Check whether answer 9 completed the assessment.
            completed_request = PHQ9AssessmentRequest(answers=graph_state.get("answers", []), notes=payload.notes)  # Build full PHQ-9 request for existing save service.
            saved_response = await run_phq9_assessment_and_save(user_id=user_id, request=completed_request)  # Save completed assessment to MongoDB.
            graph_state["result"] = saved_response.result.model_dump()  # Replace graph result with saved service result.
            graph_state["crisis_support"] = saved_response.result.crisis_support.model_dump() if saved_response.result.crisis_support else None  # Return crisis support if present.

        return _build_conversation_response(dict(graph_state))  # Convert final graph state into API response.
    except HTTPException:  # Preserve known HTTP errors.
        raise  # Re-raise known HTTP errors unchanged.
    except ValueError as exc:  # Catch validation-style errors from schema construction.
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))  # Return 422 for bad conversation state.
    except Exception:  # Catch unexpected errors.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to continue PHQ-9 conversation")  # Return safe generic 500.


@router.get("/phq9/history", response_model=PHQ9AssessmentHistoryResponse, status_code=status.HTTP_200_OK)  # Keep existing PHQ-9 history endpoint.
async def see_phq9_history(  # Define async route handler for PHQ-9 history.
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of PHQ-9 history records to return"),  # Validate page size.
    skip: int = Query(default=0, ge=0, description="Number of PHQ-9 history records to skip"),  # Validate pagination offset.
    user: Dict[str, Any] = Depends(search_user),  # Require authenticated access token.
) -> PHQ9AssessmentHistoryResponse:  # Return typed history response.
    user_id = _get_authenticated_user_id(user)  # Read and validate authenticated user ID.
    try:  # Start protected history service call.
        history_items = await get_phq9_history(user_id=user_id, limit=limit, skip=skip)  # Fetch paginated PHQ-9 history.
        return PHQ9AssessmentHistoryResponse(count=len(history_items), limit=limit, skip=skip, items=history_items)  # Return wrapped history response.
    except HTTPException:  # Preserve known HTTP errors.
        raise  # Re-raise known HTTP errors unchanged.
    except Exception:  # Catch unexpected errors.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch PHQ-9 assessment history")  # Return safe generic 500.