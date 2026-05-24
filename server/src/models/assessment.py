from datetime import datetime,timezone
from typing import Any,Dict
from src.schemas.assessment import PHQ9AssessmentRequest,PHQ9AssessmentResult

def _utc_now_iso()->str:
    """
    :return: Returns the current time in UTC in String
    """
    return datetime.now(timezone.utc).isoformat() # Returning the String

def create_phq9_assessment_document(
        user_id:str,
        request:PHQ9AssessmentRequest,
        result:PHQ9AssessmentResult
) -> Dict[str,Any]:

    document_created = _utc_now_iso()
    answer_list = [{"question_id":answer.question_id,"score":answer.score} for answer in request.answers]
    return {
        "user_id":user_id,
        "assessment_type": "phq9",
        "answers": answer_list,
        "notes": request.notes, # Store the optional note submitted with the PHQ-9 assessment.
        "total_score":result.total_score,
        "severity":result.severity,
        "needs_to_follow":result.needs_to_follow,
        "clinical_risk":result.clinical_risk,
        "recommendation":result.recommendation,
        "crisis_support": result.crisis_support.model_dump() if result.crisis_support else None, # Store structured crisis resources only when risk is detected.
        "document_created":document_created,
        "document_updated": document_created # Store mutable update timestamp (same as created_at initially).
        } # Return completed MongoDB document.
