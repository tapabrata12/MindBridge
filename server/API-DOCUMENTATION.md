# MindBridge API Documentation

Last verified against backend code: April 23, 2026.

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
5. When access expires, call `POST /api/auth/refresh` with the current refresh token.
6. Replace both stored tokens with the response from refresh.
7. On logout, call `POST /api/auth/logout` and clear local token state.

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

curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'

curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <access_token>"
```
