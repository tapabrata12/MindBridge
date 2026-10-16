# File: server/src/schemas/report.py

from datetime import datetime  # for the created_at field
from typing import List, Optional  # labels for lists and "may be empty" fields
from pydantic import BaseModel, ConfigDict, Field  # Pydantic v2 tools
from src.schemas.assessment import PHQ9ReportResult, PHQ9CrisisSupport  # reuse shapes you already built


class ReportItem(BaseModel):  # one saved report card
    model_config = ConfigDict(extra="forbid")  # reject unknown fields, same rule as your other schemas
    report_id: str = Field(..., description="The report's own MongoDB id, as text")  # the report's own _id
    assessment_id: str = Field(..., description="Which assessment this report is about")  # the link we talked about
    report: PHQ9ReportResult  # insight text, remedies, sources
    created_at: datetime  # when it was made

class ReportListResponse(BaseModel):  # answer for "show me my saved reports"
    model_config = ConfigDict(extra="forbid")
    count: int = Field(..., ge=0, description="How many reports came back")  # 0 is allowed
    items: List[ReportItem] = Field(default_factory=list)  # newest first


class ReportResponse(BaseModel):  # answer for "make me a new report"
    model_config = ConfigDict(extra="forbid")
    crisis_detected: bool = Field(default=False, description="True means help centres, not a report")  # the field the frontend checks
    report: Optional[ReportItem] = None  # filled only when there is no crisis
    crisis_support: Optional[PHQ9CrisisSupport] = None  # filled only when there is a crisis
