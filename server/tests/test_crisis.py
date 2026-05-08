import pytest  # Import pytest so async crisis tests can run cleanly.
from src.schemas.assessment import PHQ9AssessmentRequest  # Import the PHQ-9 request schema used by the crisis test.
from src.services.assessment_service import score_phq9_assessment  # Import the PHQ-9 scoring service that creates crisis support.


@pytest.mark.asyncio  # Tell pytest this async test should run inside an event loop.
async def test_phq9_item_nine_surfaces_india_crisis_resources() -> None:  # Check that item 9 risk returns helpline resources.
    request = PHQ9AssessmentRequest(  # Build a complete PHQ-9 request.
        answers=[  # Provide all nine required PHQ-9 answers.
            {"question_id": 1, "score": 0},  # Answer question 1 with no symptom frequency.
            {"question_id": 2, "score": 0},  # Answer question 2 with no symptom frequency.
            {"question_id": 3, "score": 0},  # Answer question 3 with no symptom frequency.
            {"question_id": 4, "score": 0},  # Answer question 4 with no symptom frequency.
            {"question_id": 5, "score": 0},  # Answer question 5 with no symptom frequency.
            {"question_id": 6, "score": 0},  # Answer question 6 with no symptom frequency.
            {"question_id": 7, "score": 0},  # Answer question 7 with no symptom frequency.
            {"question_id": 8, "score": 0},  # Answer question 8 with no symptom frequency.
            {"question_id": 9, "score": 1},  # Answer question 9 with a positive self-harm signal.
        ]  # Finish all PHQ-9 answers.
    )  # Finish request construction.

    result = await score_phq9_assessment(request)  # Score the request and generate any crisis support.

    assert result.clinical_risk is True  # Confirm the item 9 signal is flagged as clinical risk.
    assert result.crisis_support is not None  # Confirm structured crisis support is returned.
    assert result.crisis_support.crisis_detected is True  # Confirm the crisis support object marks the interruption state.
    assert [resource.name for resource in result.crisis_support.resources[:2]] == ["iCall India", "Vandrevala Foundation"]  # Confirm the India helplines are surfaced first.
