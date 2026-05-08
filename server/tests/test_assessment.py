import pytest  # Import pytest so async assessment tests can run cleanly.
from src.models.assessment import create_phq9_assessment_document  # Import the MongoDB document factory under test.
from src.schemas.assessment import PHQ9AssessmentRequest  # Import the PHQ-9 request schema used by the scoring service.
from src.services.assessment_service import score_phq9_assessment  # Import the PHQ-9 scoring function under test.


def _phq9_request(scores: list[int], notes: str | None = None) -> PHQ9AssessmentRequest:  # Build a valid PHQ-9 request from nine score values.
    return PHQ9AssessmentRequest(  # Return a fully validated PHQ-9 request object.
        answers=[{"question_id": index + 1, "score": score} for index, score in enumerate(scores)],  # Convert scores into question_id/score answer objects.
        notes=notes,  # Attach the optional note so persistence logic can be tested.
    )  # Finish request construction.


@pytest.mark.asyncio  # Tell pytest this async test should run inside an event loop.
async def test_phq9_score_ten_requires_followup() -> None:  # Check that the moderate threshold triggers follow-up.
    request = _phq9_request([2, 2, 1, 1, 1, 1, 1, 1, 0])  # Build a PHQ-9 request with total score 10 and no item-9 crisis signal.
    result = await score_phq9_assessment(request)  # Score the PHQ-9 request.

    assert result.total_score == 10  # Confirm the scoring sum is correct.
    assert result.severity == "moderate"  # Confirm score 10 maps to the moderate range.
    assert result.needs_to_follow is True  # Confirm moderate-or-higher scores trigger follow-up.
    assert result.clinical_risk is False  # Confirm this test is about severity follow-up, not crisis support.
    assert result.crisis_support is None  # Confirm crisis support is absent when item 9 is zero.


@pytest.mark.asyncio  # Tell pytest this async test should run inside an event loop.
async def test_phq9_document_persists_notes_and_crisis_support() -> None:  # Check that accepted request fields are actually saved.
    request = _phq9_request([0, 1, 1, 1, 1, 1, 1, 1, 1], notes="Symptoms were worse this week.")  # Build a request with a user note and item-9 risk.
    result = await score_phq9_assessment(request)  # Score the PHQ-9 request before document creation.
    document = create_phq9_assessment_document("user-123", request, result)  # Build the MongoDB document without touching the database.

    assert document["notes"] == "Symptoms were worse this week."  # Confirm the optional note is persisted in the document.
    assert document["crisis_support"] is not None  # Confirm crisis support is persisted when clinical risk is present.
    assert document["crisis_support"]["resources"][0]["name"] == "iCall India"  # Confirm the first saved resource is the India helpline from the spec.
