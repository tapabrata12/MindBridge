from src.core.constants import PHQ9_SEVERITY
from typing import List

def calculate_phq9_score(answers: List[int]) -> dict:
    """
    Calculates the PHQ-9 score and determines the severity level.

    Args:
        answers: A list of integers representing the patient's responses to the 9 PHQ-9 questions.
                 Each response should be an integer between 0 and 3.

    Returns:
        A dictionary containing the total score, severity level, and screening type.

    Raises:
        ValueError: If the total score is outside the valid PHQ-9 range (0-27).
    """
    total_score = sum(answers)
    severity = "Unknown"

    for min_value, max_value, label in PHQ9_SEVERITY:
        if min_value <= total_score <= max_value:
            severity = label
            break

    if severity == "Unknown":
        raise ValueError("Score out of valid PHQ-9 range")

    return {
        "total_score": total_score,
        "severity": severity,
        "screening_type": "PHQ9"
    }