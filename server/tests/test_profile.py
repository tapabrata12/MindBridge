import pytest  # Import pytest so validation failures can be asserted cleanly.
from pydantic import ValidationError  # Import Pydantic's validation error type for schema tests.
from src.schemas.user import UserProfileUpdate  # Import the profile update schema under test.


def test_profile_life_events_are_cleaned_and_capped() -> None:  # Check that profile life events are safe and bounded.
    profile = UserProfileUpdate(life_events=[" job loss ", "", "move", "exam", "illness", "breakup", "new job"])  # Build a profile with whitespace, blanks, and too many events.

    assert profile.life_events == ["job loss", "move", "exam", "illness", "breakup"]  # Confirm blanks are removed, strings are stripped, and only five remain.


def test_profile_rejects_invalid_age() -> None:  # Check that unrealistic ages are rejected by the schema.
    with pytest.raises(ValidationError):  # Capture Pydantic's validation failure.
        UserProfileUpdate(age=9)  # Try to create a profile below the allowed minimum age.
