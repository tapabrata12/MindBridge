from src.services.screening_service import calculate_phq9_score

def test_phq9_minimal_score():
    pass

def test_phq9_boundary_mild_transition():
    answers_4 = [1,1,1,1,0,0,0,0,0]
    answers_5 = [1,1,1,1,1,0,0,0,0]

    result_4 = calculate_phq9_score(answers_4)
    result_5 = calculate_phq9_score(answers_5)

    assert result_4["severity"] == "Minimal"
    assert result_5["severity"] == "Mild"