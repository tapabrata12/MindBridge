from pydantic import BaseModel,Field
from typing import List
from typing_extensions import Annotated

AnswerValue = Annotated[int,Field(ge=0, le=3)]

class PHQ9Request(BaseModel):
    """
    Request model for PHQ-9 screening.
    """
    answers: Annotated[List[AnswerValue],Field(max_length=9, min_length=9)]

class PHQ9Response(BaseModel):
    """
    Response model for PHQ-9 screening.
    """
    total_score: int
    severity: str
    screening_type: str