# File: server/src/schemas/assessment.py  # Full file path comment as requested
from pydantic import BaseModel,model_validator,field_validator,ConfigDict,Field # Import Pydantic v2 tools for schema validation and configuration
from typing import Optional,Literal,List # Import typing helpers for strict literal values and optional fields

PHQ9AnswerValue = Literal[0,1,2,3] # Define allowed PHQ-9 answer values where 0=not at all and 3=nearly every day
PHQ9QuestionID = Literal[1,2,3,4,5,6,7,8,9] # Define strict question identifiers for PHQ-9 questions one through nine
PHQ9Severity = Literal["minimal", "mild", "moderate", "moderately_severe", "severe"]  # Define standard PHQ-9 score interpretation bands

class PHQ9QuestionAnswer(BaseModel):  # Define schema for a single PHQ-9 question answer item
    model_config = ConfigDict(extra="forbid",str_strip_whitespace=True)  # Reject unknown fields and strip whitespace from input strings
    question_id:PHQ9QuestionID = Field(..., description="PHQ-9 question number from 1 to 9")  # Require a valid PHQ-9 question identifier
    score: PHQ9AnswerValue = Field(...,description="PHQ-9 score value: 0, 1, 2, or 3")  # Require a valid PHQ-9 per-question score

class PHQ9AssessmentRequest(BaseModel): # Define schema for submitting a complete PHQ-9 screener response
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    answers:List[PHQ9QuestionAnswer] = Field(..., min_length=9, max_length=9, description="Exactly 9 PHQ-9 answers in a single submission") # Require exactly nine answers for a complete PHQ-9 run
    notes: Optional[str] = Field(None, min_length=1, max_length=1000, description="Optional short user note to store with this assessment") # Allow an optional note for additional context
    @field_validator('answers')
    @classmethod
    def validate_answer_length(cls, value:List[PHQ9QuestionAnswer])-> List[PHQ9QuestionAnswer]:
        pass