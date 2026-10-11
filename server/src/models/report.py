from datetime import datetime, timezone
from typing import Any, Dict
from src.schemas.assessment import PHQ9ReportResult

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create_phq9_report_document(user_id: str, assessment_id: str, report: PHQ9ReportResult) -> Dict[str, Any]:
    pass