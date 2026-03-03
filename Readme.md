# Mental Health Companion API Documentation

## Screening API

### PHQ-9 Screening Endpoint

**Endpoint:** `POST /api/v1/screening/phq9`  
**Tags:** `Screening`

This endpoint calculates the PHQ-9 (Patient Health Questionnaire-9) depression severity score based on the user's responses.

#### Description
At the time of User Screening, the user will tick a certain value for each of the 9 standard PHQ-9 questions. This endpoint accepts the array of answers, validates them, calculates the total score, and returns the interpreted severity level.

#### Schema Data Validation & Constraints (Enterprise Grade)

The endpoint relies on rigorous constraints implemented via Pydantic (`PHQ9Request`):

**Request Payload Constraints:**
- **`answers` (List[int])**: Must be an array containing exactly **9 integers**.
  - `min_length=9`: Rejects requests with fewer than 9 answers to ensure completion.
  - `max_length=9`: Rejects requests with more than 9 answers.
- **Answer Value Constraints (`AnswerValue`)**: Each integer in the array must be strictly between `0` and `3` inclusive (`ge=0, le=3`). These values correspond to the frequency of the symptoms:
  * `0`: Not at all
  * `1`: Several days
  * `2`: More than half the days
  * `3`: Nearly every day

#### Request Example

```json
{
  "answers": [1, 1, 1, 1, 0, 0, 0, 0, 0]
}
```

#### Response Structure (`PHQ9Response`)

The API returns a JSON object containing the computed result:

- **`total_score` (int)**: The sum of all values in the `answers` array (Range: `0` to `27`).
- **`severity` (str)**: The mapped psychological severity label based on the `total_score`.
- **`screening_type` (str)**: Always returns `"PHQ9"` for this endpoint to cleanly identify the context on the client-side.

#### Severity Mapping Rules

The `total_score` is mapped to severity defined in the `src/core/constants.py` (`PHQ9_SEVERITY`):

| Total Score Range | Severity Label      |
|-------------------|---------------------|
| 0 - 4             | Minimal             |
| 5 - 9             | Mild                |
| 10 - 14           | Moderate            |
| 15 - 19           | Moderately Severe   |
| 20 - 27           | Severe              |

#### Validation/Error Responses
If the input violates schema constraints (e.g., answering fewer than 9 questions, or providing an out-of-range value such as `4` for any question), FastAPI will automatically reject the request and throw an HTTP `422 Unprocessable Entity` detailed validation error. The core business logic will also throw a `ValueError` if the severity fails to map correctly.
