from src.models.report import create_phq9_report_document
from src.schemas.assessment import PHQ9ReportResult

def test_docs_is_building_correctly():
    fake_report = PHQ9ReportResult(insight_report="Test Insight", remedies=["Morning Work", "Laughing", "Work Hard"], sources=["mhGAP.pdf"])
    doc = create_phq9_report_document(user_id="user123", assessment_id="assessment456", report=fake_report)
    assert doc["user_id"] == "user123"  # the owner must match what we passed in
    assert doc["assessment_id"] == "assessment456"  # the link must match too
    assert doc["report"]["remedies"] == ["Morning Work", "Laughing", "Work Hard"]  # the report content must be copied correctly
    assert isinstance(doc["created_at"], str)  # the time stamp must be text