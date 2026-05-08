# MindBridge API Documentation

Last verified against backend code: May 8, 2026.

Base URL:

```text
http://localhost:8000/api
```

Interactive documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Authentication scheme:

```text
Authorization: Bearer <access_token>
```

The backend uses JWT access tokens and server-stored refresh tokens.

## Endpoint Summary

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | No | Root service status. |
| `GET` | `/health` | No | Health check. |
| `POST` | `/api/auth/register` | No | Register a new user and return a token pair. |
| `POST` | `/api/auth/login` | No | Login and return a token pair. |
| `POST` | `/api/auth/login/swagger` | No | Swagger OAuth2 form login. |
| `GET` | `/api/auth/me` | Yes | Return the authenticated user's email. |
| `POST` | `/api/auth/refresh` | No | Rotate refresh token and return a new token pair. |
| `POST` | `/api/auth/logout` | Yes | Revoke all sessions for the authenticated user. |
| `GET` | `/api/profile` | Yes | Get the authenticated user's profile. |
| `PUT` | `/api/profile` | Yes | Replace the authenticated user's profile. |
| `POST` | `/api/assessment/phq9` | Yes | Score and save a PHQ-9 assessment. |
| `GET` | `/api/assessment/phq9/history` | Yes | Get paginated PHQ-9 assessment history. |

## Token Model

| Token | Default TTL | Stored server-side | Purpose |
|---|---:|---:|---|
| Access token | 15 minutes | No | Authorizes protected API requests. |
| Refresh token | 7 days | Yes, in `refresh_tokens` | Rotates session and issues new token pair. |

JWT payloads include:

- `sub`: user email
- `exp`: expiration timestamp
- `type`: `access` or `refresh`
- `iat`: issued-at timestamp

Refresh behavior:

1. Client sends an active refresh token to `/api/auth/refresh`.
2. Server validates signature, expiry, `sub`, user existence, and server-side token presence.
3. Server removes the old refresh token with `$pull`.
4. Server stores a new refresh token with `$push`.
5. Server returns a new access token and a new refresh token.

Logout behavior:

- `POST /api/auth/logout` clears all stored refresh tokens for the authenticated user.
- Protected routes also require the user to still have at least one active refresh token.
- After logout, protected endpoints return `401` even if the old access token has not expired yet.

## Public Service Endpoints

### GET /

Returns a simple service status response.

Auth required: No

Success response:

```json
{
  "message": "MindBridge API is running"
}
```

### GET /health

Returns a simple health response.

Auth required: No

Success response:

```json
{
  "status": "ok"
}
```

## Authentication Endpoints

### POST /api/auth/register

Registers a new user and returns an access/refresh token pair.

Auth required: No

Request body:

```json
{
  "email": "alice@example.com",
  "password": "S3cur3P@ssw0rd"
}
```

Request constraints:

| Field | Type | Required | Constraint |
|---|---|---:|---|
| `email` | email string | Yes | Must be valid email format. |
| `password` | string | Yes | 8 to 72 characters. |

Extra request fields are rejected.

Success response `201`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Errors:

| Status | Meaning | Example detail |
|---:|---|---|
| `409` | Email already exists | `User already exists` |
| `422` | Request validation failed | FastAPI validation error array |

Example:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"S3cur3P@ssw0rd"}'
```

### POST /api/auth/login

Authenticates an existing user and returns a token pair.

Auth required: No

Request body:

```json
{
  "email": "alice@example.com",
  "password": "S3cur3P@ssw0rd"
}
```

Success response `200`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Errors:

| Status | Meaning | Example detail |
|---:|---|---|
| `401` | Email not found or password mismatch | `Incorrect email or password` |
| `422` | Request validation failed | FastAPI validation error array |

Example:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"S3cur3P@ssw0rd"}'
```

### POST /api/auth/login/swagger

OAuth2 password-form login endpoint used by Swagger UI's Authorize button.

Use `/api/auth/login` for normal JSON clients.

Auth required: No

Content type:

```text
application/x-www-form-urlencoded
```

Form fields:

| Field | Meaning |
|---|---|
| `username` | User email address. |
| `password` | User password. |

Success response `200`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Errors:

| Status | Meaning | Example detail |
|---:|---|---|
| `401` | Invalid credentials | `Incorrect email or password` |

### GET /api/auth/me

Returns the authenticated user's email address.

Auth required: Yes

Headers:

```text
Authorization: Bearer <access_token>
```

Success response `200`:

```json
{
  "email": "alice@example.com"
}
```

Errors:

| Status | Meaning | Example detail |
|---:|---|---|
| `401` | Missing, invalid, expired, or revoked session | `Invalid or expired token` |
| `401` | No active refresh token remains for this user | `Session expired, please login again` |
| `500` | Stored user token data is malformed | `Invalid user token store` |

Example:

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### POST /api/auth/refresh

Rotates a valid refresh token and returns a new token pair.

Auth required: No

Request body:

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Request constraints:

| Field | Type | Required | Constraint |
|---|---|---:|---|
| `refresh_token` | string | Yes | Minimum length 20. |

Success response `200`:

```json
{
  "access_token": "new-access-token",
  "refresh_token": "new-refresh-token",
  "token_type": "bearer"
}
```

Important: the old refresh token is removed from MongoDB and cannot be reused.

Errors:

| Status | Meaning | Example detail |
|---:|---|---|
| `401` | Refresh token invalid, expired, revoked, reused, or not linked to a user | `Invalid or expired refresh token` |
| `422` | Request validation failed | FastAPI validation error array |

Example:

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

### POST /api/auth/logout

Revokes all refresh tokens for the authenticated user.

Auth required: Yes

Headers:

```text
Authorization: Bearer <access_token>
```

Success response `200`:

```json
{
  "message": "Successfully logged out"
}
```

Already logged out response `200`:

```json
{
  "message": "Already logged out"
}
```

Errors:

| Status | Meaning | Example detail |
|---:|---|---|
| `401` | Missing, invalid, expired, or malformed access token | `Invalid or expired token` |
| `404` | User no longer exists | `User not found` |

Example:

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

## Profile Endpoints

Profile endpoints use the authenticated user's ID from the access token dependency. Clients do not pass a user ID in the URL.

### GET /api/profile

Returns the authenticated user's profile object.

Auth required: Yes

Headers:

```text
Authorization: Bearer <access_token>
```

Success response `200`:

```json
{
  "age": 28,
  "gender": "female",
  "occupation": "working",
  "sleep_hours": 7,
  "social_support": "medium",
  "life_events": ["changed jobs", "relocated"]
}
```

Default profile response for a new user:

```json
{
  "age": null,
  "gender": null,
  "occupation": null,
  "sleep_hours": null,
  "social_support": null,
  "life_events": []
}
```

Errors:

| Status | Meaning | Example detail |
|---:|---|---|
| `401` | Missing, invalid, expired, or revoked session | `Session expired, please login again` |
| `400` | Authenticated user ID is malformed | `Invalid user ID` |
| `404` | User or profile not found | `User not found` / `Profile not found` |
| `500` | Unexpected database/service failure | `Failed to fetch profile: ...` |

Example:

```bash
curl http://localhost:8000/api/profile \
  -H "Authorization: Bearer <access_token>"
```

### PUT /api/profile

Replaces the authenticated user's stored profile with validated profile data.

Auth required: Yes

Headers:

```text
Authorization: Bearer <access_token>
Content-Type: application/json
```

Request body:

```json
{
  "age": 28,
  "gender": "female",
  "occupation": "working",
  "sleep_hours": 7,
  "social_support": "medium",
  "life_events": ["changed jobs", "relocated"]
}
```

Important current behavior:

- The route uses `PUT`, not `PATCH`.
- The service stores `profile_details.model_dump()` as the full `profile` object.
- Omitted fields are saved as their schema defaults, usually `null` or `[]`.
- Extra fields are rejected.

Success response `200`:

```json
{
  "age": 28,
  "gender": "female",
  "occupation": "working",
  "sleep_hours": 7,
  "social_support": "medium",
  "life_events": ["changed jobs", "relocated"]
}
```

Errors:

| Status | Meaning | Example detail |
|---:|---|---|
| `400` | Authenticated user ID is malformed | `Invalid user ID` |
| `401` | Missing, invalid, expired, or revoked session | `Invalid or expired token` |
| `404` | User not found | `User not found` |
| `422` | Profile validation failed | FastAPI validation error array |
| `500` | Unexpected database/service failure | `Failed to update profile: ...` |

Example:

```bash
curl -X PUT http://localhost:8000/api/profile \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 28,
    "gender": "female",
    "occupation": "working",
    "sleep_hours": 7,
    "social_support": "medium",
    "life_events": ["changed jobs", "relocated"]
  }'
```

## Assessment Endpoints

Assessment endpoints are protected and currently support PHQ-9 only.

### POST /api/assessment/phq9

Scores a PHQ-9 submission, saves it to the assessment collection, and returns the computed result.

Auth required: Yes

Headers:

```text
Authorization: Bearer <access_token>
Content-Type: application/json
```

Request body:

```json
{
  "answers": [
    {"question_id": 1, "score": 1},
    {"question_id": 2, "score": 2},
    {"question_id": 3, "score": 1},
    {"question_id": 4, "score": 2},
    {"question_id": 5, "score": 1},
    {"question_id": 6, "score": 2},
    {"question_id": 7, "score": 1},
    {"question_id": 8, "score": 1},
    {"question_id": 9, "score": 1}
  ],
  "notes": "Symptoms have been worse this week."
}
```

Request constraints:

| Field | Type | Required | Constraint |
|---|---|---:|---|
| `answers` | array | Yes | Exactly 9 items. |
| `answers[].question_id` | integer | Yes | Must include each value `1` through `9` exactly once. |
| `answers[].score` | integer | Yes | Allowed values: `0`, `1`, `2`, `3`. |
| `notes` | string or null | No | If provided, 1 to 1000 characters. |

Scoring behavior:

- `total_score` is the sum of all 9 answer scores.
- `severity` is derived from the total score:

| Total score | Severity |
|---:|---|
| `0` to `4` | `minimal` |
| `5` to `9` | `mild` |
| `10` to `14` | `moderate` |
| `15` to `19` | `moderately_severe` |
| `20` to `27` | `severe` |

- `clinical_risk` is `true` when question `9` has a score greater than `0`.
- `needs_to_follow` is `true` when `total_score >= 10` or `clinical_risk` is `true`.
- The recommendation message changes based on the follow-up and crisis-risk flags.
- `crisis_support` is included when `clinical_risk` is `true`.

Important current behavior:

- The route saves the computed assessment result to MongoDB.
- The saved document includes answers, notes, score, severity, follow-up flags, recommendation, crisis support, and timestamps.
- Extra request fields are rejected.

Success response `200`:

```json
{
  "assessment_type": "phq9",
  "result": {
    "total_score": 12,
    "severity": "moderate",
    "needs_to_follow": true,
    "clinical_risk": true,
    "recommendation": "Your responses suggest possible immediate safety concerns. Please contact local emergency services or a crisis helpline now, and share this screening with a trusted clinician.",
    "crisis_support": {
      "crisis_detected": true,
      "message": "Your answer suggests possible self-harm risk. Please contact emergency services or a crisis helpline now, and reach out to someone you trust.",
      "resources": [
        {
          "name": "iCall India",
          "contact": "9152987821",
          "region": "India"
        },
        {
          "name": "Vandrevala Foundation",
          "contact": "1860-2662-345",
          "region": "India"
        },
        {
          "name": "Local emergency services",
          "contact": "Contact your local emergency number immediately if you are in immediate danger",
          "region": "Local"
        }
      ]
    }
  }
}
```

Errors:

| Status | Meaning | Example detail |
|---:|---|---|
| `401` | Missing, invalid, expired, or revoked session | `Invalid or expired token` / `Session expired, please login again` |
| `400` | Authenticated user ID is malformed | `User id is invalid or empty` |
| `422` | Request validation failed | FastAPI validation error array |
| `500` | Database or processing failure | `Database connection is not initialized` / `Failed to save assessment` |

Example:

```bash
curl -X POST http://localhost:8000/api/assessment/phq9 \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question_id": 1, "score": 1},
      {"question_id": 2, "score": 2},
      {"question_id": 3, "score": 1},
      {"question_id": 4, "score": 2},
      {"question_id": 5, "score": 1},
      {"question_id": 6, "score": 2},
      {"question_id": 7, "score": 1},
      {"question_id": 8, "score": 1},
      {"question_id": 9, "score": 1}
    ],
    "notes": "Symptoms have been worse this week."
  }'
```

### GET /api/assessment/phq9/history

Returns paginated PHQ-9 assessment history for the authenticated user.

Auth required: Yes

Headers:

```text
Authorization: Bearer <access_token>
```

Query parameters:

| Name | Type | Required | Default | Constraint |
|---|---|---:|---:|---|
| `limit` | integer | No | `20` | `1` to `100` |
| `skip` | integer | No | `0` | `0` or greater |

Important current behavior:

- Results are filtered by the authenticated user only.
- Results are sorted by `document_created` descending, so newest items are returned first.
- The response includes persisted result metadata, saved notes, and crisis support when present.

Success response `200`:

```json
{
  "assessment_type": "phq9",
  "count": 2,
  "limit": 20,
  "skip": 0,
  "items": [
    {
      "assessment_id": "681bf5e0c0a6c43c09b2f101",
      "assessment_type": "phq9",
      "total_score": 12,
      "severity": "moderate",
      "needs_to_follow": true,
      "clinical_risk": false,
      "recommendation": "Your PHQ-9 result falls in the moderate range. Please schedule a professional mental health follow-up and continue regular check-ins.",
      "notes": "Symptoms have been worse this week.",
      "crisis_support": null,
      "created_at": "2026-05-08T03:20:15.123456+00:00"
    },
    {
      "assessment_id": "681bf490c0a6c43c09b2f0ff",
      "assessment_type": "phq9",
      "total_score": 7,
      "severity": "mild",
      "needs_to_follow": false,
      "clinical_risk": false,
      "recommendation": "Your responses are currently in a lower-severity range. Keep practicing daily self-care and repeat this check-in if symptoms increase.",
      "notes": null,
      "crisis_support": null,
      "created_at": "2026-05-07T17:42:08.481922+00:00"
    }
  ]
}
```

Errors:

| Status | Meaning | Example detail |
|---:|---|---|
| `401` | Missing, invalid, expired, or revoked session | `Invalid or expired token` / `Session expired, please login again` |
| `400` | Authenticated user ID is malformed | `User id is invalid or empty` |
| `422` | Query parameter validation failed | FastAPI validation error array |
| `500` | Database or history retrieval failure | `Database connection is not initialized` / `Failed to fetch PHQ-9 assessment history` |

Example:

```bash
curl "http://localhost:8000/api/assessment/phq9/history?limit=20&skip=0" \
  -H "Authorization: Bearer <access_token>"
```

## Data Schemas

### UserCreate

Used by `POST /api/auth/register`.

```json
{
  "email": "alice@example.com",
  "password": "S3cur3P@ssw0rd"
}
```

Rules:

- `email` must be a valid email address.
- `password` must be 8 to 72 characters.
- Unknown fields are rejected.
- String whitespace is stripped.

### UserLogin

Used by `POST /api/auth/login`.

```json
{
  "email": "alice@example.com",
  "password": "S3cur3P@ssw0rd"
}
```

Rules:

- `email` must be a valid email address.
- `password` must be 8 to 72 characters.
- Unknown fields are rejected.
- String whitespace is stripped.

### RefreshRequest

Used by `POST /api/auth/refresh`.

```json
{
  "refresh_token": "<refresh_token>"
}
```

Rules:

- `refresh_token` must be a string.
- Minimum length is 20.
- Unknown fields are rejected.
- String whitespace is stripped.

### TokenResponse

Returned by register, login, Swagger login, and refresh.

```json
{
  "access_token": "<access_token>",
  "refresh_token": "<refresh_token>",
  "token_type": "bearer"
}
```

### UserResponse

Returned by `GET /api/auth/me`.

```json
{
  "email": "alice@example.com"
}
```

### UserProfileUpdate

Used by `PUT /api/profile`.

| Field | Type | Required | Allowed values / range |
|---|---|---:|---|
| `age` | integer or null | No | `10` to `100` |
| `gender` | string or null | No | `male`, `female`, `other` |
| `occupation` | string or null | No | `student`, `working`, `unemployed`, `retired`, `other` |
| `sleep_hours` | integer or null | No | `0` to `24` |
| `social_support` | string or null | No | `high`, `medium`, `low` |
| `life_events` | string array or null | No | Empty values removed, max 5 stored |

Example:

```json
{
  "age": 28,
  "gender": "female",
  "occupation": "working",
  "sleep_hours": 7,
  "social_support": "medium",
  "life_events": ["changed jobs", "relocated"]
}
```

### UserProfileResponse

Returned by `GET /api/profile` and `PUT /api/profile`.

```json
{
  "age": 28,
  "gender": "female",
  "occupation": "working",
  "sleep_hours": 7,
  "social_support": "medium",
  "life_events": ["changed jobs", "relocated"]
}
```

### PHQ9QuestionAnswer

Used inside `PHQ9AssessmentRequest.answers`.

| Field | Type | Required | Allowed values / range |
|---|---|---:|---|
| `question_id` | integer | Yes | `1` through `9` |
| `score` | integer | Yes | `0`, `1`, `2`, `3` |

### PHQ9AssessmentRequest

Used by `POST /api/assessment/phq9`.

```json
{
  "answers": [
    {"question_id": 1, "score": 1},
    {"question_id": 2, "score": 2},
    {"question_id": 3, "score": 1},
    {"question_id": 4, "score": 2},
    {"question_id": 5, "score": 1},
    {"question_id": 6, "score": 2},
    {"question_id": 7, "score": 1},
    {"question_id": 8, "score": 1},
    {"question_id": 9, "score": 1}
  ],
  "notes": "Symptoms have been worse this week."
}
```

Rules:

- `answers` must contain exactly 9 items.
- The set of `question_id` values must be exactly `1` through `9`, with no duplicates or omissions.
- Each `score` must be one of `0`, `1`, `2`, or `3`.
- `notes` is optional; if provided, it must be 1 to 1000 characters.
- Unknown fields are rejected.
- String whitespace is stripped.

### PHQ9AssessmentResult

Returned as the `result` field in `PHQ9AssessmentResponse`.

| Field | Type | Meaning |
|---|---|---|
| `total_score` | integer | Sum of all 9 PHQ-9 answer scores, from `0` to `27`. |
| `severity` | string | One of `minimal`, `mild`, `moderate`, `moderately_severe`, `severe`. |
| `needs_to_follow` | boolean | `true` when `total_score >= 10` or question `9` has a score greater than `0`. |
| `clinical_risk` | boolean | `true` when question `9` has a score greater than `0`. |
| `recommendation` | string | Computed guidance message based on severity and risk flags. |
| `crisis_support` | object or null | Structured crisis guidance and helplines when `clinical_risk` is `true`. |

### PHQ9AssessmentResponse

Returned by `POST /api/assessment/phq9`.

```json
{
  "assessment_type": "phq9",
  "result": {
    "total_score": 12,
    "severity": "moderate",
    "needs_to_follow": true,
    "clinical_risk": true,
    "recommendation": "Your responses suggest possible immediate safety concerns. Please contact local emergency services or a crisis helpline now, and share this screening with a trusted clinician.",
    "crisis_support": {
      "crisis_detected": true,
      "message": "Your answer suggests possible self-harm risk. Please contact emergency services or a crisis helpline now, and reach out to someone you trust.",
      "resources": [
        {
          "name": "iCall India",
          "contact": "9152987821",
          "region": "India"
        },
        {
          "name": "Vandrevala Foundation",
          "contact": "1860-2662-345",
          "region": "India"
        },
        {
          "name": "Local emergency services",
          "contact": "Contact your local emergency number immediately if you are in immediate danger",
          "region": "Local"
        }
      ]
    }
  }
}
```

### PHQ9AssessmentHistoryItem

Used inside `PHQ9AssessmentHistoryResponse.items`.

| Field | Type | Meaning |
|---|---|---|
| `assessment_id` | string | MongoDB assessment document ID as a string. |
| `assessment_type` | string | Always `phq9`. |
| `total_score` | integer | Saved PHQ-9 total score. |
| `severity` | string | Saved severity label. |
| `needs_to_follow` | boolean | Saved follow-up flag. |
| `clinical_risk` | boolean | Saved clinical-risk flag. |
| `recommendation` | string | Saved recommendation text. |
| `notes` | string or null | Optional note saved with the assessment. |
| `crisis_support` | object or null | Saved crisis resources when clinical risk was triggered. |
| `created_at` | ISO datetime string or null | Saved creation timestamp when available. |

### PHQ9AssessmentHistoryResponse

Returned by `GET /api/assessment/phq9/history`.

```json
{
  "assessment_type": "phq9",
  "count": 2,
  "limit": 20,
  "skip": 0,
  "items": [
    {
      "assessment_id": "681bf5e0c0a6c43c09b2f101",
      "assessment_type": "phq9",
      "total_score": 12,
      "severity": "moderate",
      "needs_to_follow": true,
      "clinical_risk": false,
      "recommendation": "Your PHQ-9 result falls in the moderate range. Please schedule a professional mental health follow-up and continue regular check-ins.",
      "created_at": "2026-05-08T03:20:15.123456+00:00"
    }
  ]
}
```

## Error Format

Most application errors use FastAPI's standard error envelope:

```json
{
  "detail": "Human readable message"
}
```

Validation errors use FastAPI/Pydantic's validation format:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "input": "short"
    }
  ]
}
```

Common status codes:

| Status | Typical cause |
|---:|---|
| `200` | Request succeeded. |
| `201` | User registration succeeded. |
| `400` | Authenticated user ID is malformed. |
| `401` | Missing/invalid/expired token, revoked session, or wrong credentials. |
| `404` | User or profile not found. |
| `409` | Email already registered. |
| `422` | Request body validation failed. |
| `500` | Unexpected server/database state. |

## Example Client Flow

1. Register or login.
2. Store the returned `access_token` for API authorization.
3. Store the returned `refresh_token` securely.
4. Call protected endpoints with `Authorization: Bearer <access_token>`.
5. Submit PHQ-9 assessments with `POST /api/assessment/phq9` when needed.
6. Read saved PHQ-9 history with `GET /api/assessment/phq9/history`.
7. When access expires, call `POST /api/auth/refresh` with the current refresh token.
8. Replace both stored tokens with the response from refresh.
9. On logout, call `POST /api/auth/logout` and clear local token state.

Example sequence:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"S3cur3P@ssw0rd"}'

curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"

curl -X PUT http://localhost:8000/api/profile \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"age":28,"gender":"female","occupation":"working","sleep_hours":7,"social_support":"medium","life_events":["changed jobs"]}'

curl -X POST http://localhost:8000/api/assessment/phq9 \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question_id":1,"score":1},
      {"question_id":2,"score":2},
      {"question_id":3,"score":1},
      {"question_id":4,"score":2},
      {"question_id":5,"score":1},
      {"question_id":6,"score":2},
      {"question_id":7,"score":1},
      {"question_id":8,"score":1},
      {"question_id":9,"score":1}
    ],
    "notes":"Symptoms have been worse this week."
  }'

curl "http://localhost:8000/api/assessment/phq9/history?limit=20&skip=0" \
  -H "Authorization: Bearer <access_token>"

curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'

curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <access_token>"
```
