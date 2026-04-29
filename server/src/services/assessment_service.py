# File: server/src/services/assessment_service.py
from typing import Tuple
from src.schemas.assessment import PHQ9Severity,PHQ9AssessmentRequest
def _determine_phq9_severity(total_score:int)->PHQ9Severity:
    """
    :param total_score: int
    :return String: PHQ9Severity
    :Workings: It takes the total PHQ-9 score and returns message according to that score
    """
    if 0 <= total_score <= 4:
        return PHQ9Severity("minimal")

    elif 5 <= total_score <= 9:
        return PHQ9Severity("mild")

    elif 10 <= total_score <= 14:
        return PHQ9Severity("moderate")

    elif 15<= total_score <= 19:
        return PHQ9Severity("moderately_severe")

    return PHQ9Severity("severe")

def _evaluate_follow_up_flags(question:PHQ9AssessmentRequest):
    pass