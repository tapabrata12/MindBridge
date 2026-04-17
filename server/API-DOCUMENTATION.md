# Mental Health Companion — API Reference

> **Base URL:** `http://localhost:8000/api`  
> **Interactive Docs:** `http://localhost:8000/docs` (Swagger UI) · `http://localhost:8000/redoc` (ReDoc)  
> **Auth scheme:** JWT Bearer (HS256) — access token (1 min TTL) + refresh token (7 day TTL)

---

## Table of Contents

- [Authentication Overview](#authentication-overview)
- [Endpoints](#endpoints)
  - [POST /auth/register](#post-authregister)
  - [POST /auth/login](#post-authlogin)
  - [POST /auth/login/swagger](#post-authloginswagger)
  - [GET /auth/profile](#get-authprofile)
  - [POST /auth/refresh](#post-authrefresh)
  - [GET /auth/logout](#get-authlogout)
- [Data Schemas](#data-schemas)
- [Error Reference](#error-reference)
- [Token Lifecycle](#token-lifecycle)

---

## Authentication Overview

This API uses a **dual-token JWT strategy**:

| Token | TTL | Purpose |
|---|---|---|
| `access_token` | 1 minute (configurable) | Authorizes protected API requests |
| `refresh_token` | 7 days (configurable) | Issues new access tokens without re-login |

### How to authenticate a request

Pass the access token in the `Authorization` header of every protected request:

```
Authorization: Bearer <access_token>
```

### Token flow

```
Register / Login
      │
      ▼
 access_token (1 min) ──► use in Authorization header
 refresh_token (7 days) ─► store securely (e.g., httpOnly cookie / secure storage)
      │
      ▼ (when access token expires)
 POST /auth/refresh  ──► new access_token (refresh_token unchanged)
      │
      ▼ (when done)
 GET /auth/logout ──► server clears refresh_tokens[] (all sessions invalidated)
```

> **Security note:** Refresh tokens are stored server-side in MongoDB. Logout invalidates them immediately, even if they have not yet expired.

---

## Endpoints

---

### POST /auth/register

Register a new user account and receive a token pair.

**Accepts:** `application/json`  
**Auth required:** No

#### Request Body

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `email` | string (email) | ✅ | Valid email format | Must be unique in the system |
| `password` | string | ✅ | 8–72 characters | Stored as bcrypt hash |

#### Responses

| Status | Meaning |
|---|---|
| `201 Created` | User registered. Access and refresh tokens returned. |
| `409 Conflict` | An account with this email already exists. |
| `422 Unprocessable Entity` | Schema validation failed (e.g. password too short). |

#### Example Request + Response

<details>
<summary><strong>cURL</strong></summary>

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "S3cur3P@ssw0rd"
  }'
```
</details>

<details>
<summary><strong>JavaScript (fetch)</strong></summary>

```javascript
const response = await fetch("http://localhost:8000/api/auth/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "alice@example.com",
    password: "S3cur3P@ssw0rd",
  }),
});

const data = await response.json();
// data.content.access_token  ← store this
// data.content.refresh_token ← store this securely
```
</details>

<details>
<summary><strong>Python (httpx)</strong></summary>

```python
import httpx

r = httpx.post(
    "http://localhost:8000/api/auth/register",
    json={"email": "alice@example.com", "password": "S3cur3P@ssw0rd"},
)
tokens = r.json()["content"]
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]
```
</details>

**Success Response `201`:**
```json
{
  "message": "User successfully registered",
  "content": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

**Error Response `409`:**
```json
{
  "detail": "User already exists"
}
```

**Error Response `422`:**
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "type": "string_too_short"
    }
  ]
}
```

---

### POST /auth/login

Authenticate an existing user and receive a fresh token pair.

**Accepts:** `application/json`  
**Auth required:** No

#### Request Body

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | string (email) | ✅ | Registered email address |
| `password` | string | ✅ | Account password (plain text, verified against bcrypt hash) |

#### Responses

| Status | Meaning |
|---|---|
| `200 OK` | Credentials valid. Access and refresh tokens returned. |
| `401 Unauthorized` | Email not found **or** password mismatch. |
| `422 Unprocessable Entity` | Schema validation failed. |

> **Note:** For security, a generic `401` is returned for both "user not found" and "wrong password" — the API does not distinguish between them.

#### Example Request + Response

<details>
<summary><strong>cURL</strong></summary>

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "S3cur3P@ssw0rd"
  }'
```
</details>

<details>
<summary><strong>JavaScript (fetch)</strong></summary>

```javascript
const response = await fetch("http://localhost:8000/api/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "alice@example.com",
    password: "S3cur3P@ssw0rd",
  }),
});

if (!response.ok) {
  const err = await response.json();
  throw new Error(err.detail); // "Incorrect email or password"
}

const { content } = await response.json();
localStorage.setItem("access_token", content.access_token);
```
</details>

<details>
<summary><strong>Python (httpx)</strong></summary>

```python
import httpx

r = httpx.post(
    "http://localhost:8000/api/auth/login",
    json={"email": "alice@example.com", "password": "S3cur3P@ssw0rd"},
)
r.raise_for_status()
tokens = r.json()["content"]
```
</details>

**Success Response `200`:**
```json
{
  "message": "User successfully logged in",
  "content": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

**Error Response `401`:**
```json
{
  "detail": "Incorrect email or password"
}
```

---

### POST /auth/login/swagger

> ⚠️ **For Swagger UI (`/docs`) use only.** Use `POST /auth/login` in all production clients.

Accepts `application/x-www-form-urlencoded` (OAuth2 Password Grant) to enable the Swagger UI **Authorize** button. The `username` field maps to the user's email address.

**Accepts:** `application/x-www-form-urlencoded`  
**Auth required:** No

#### Form Fields

| Field | Type | Description |
|---|---|---|
| `username` | string | The user's email address (`username` per OAuth2 spec) |
| `password` | string | Account password |

#### Responses

| Status | Meaning |
|---|---|
| `200 OK` | Token pair returned (no wrapping `message`/`content` envelope). |
| `401 Unauthorized` | Invalid credentials. |

**Success Response `200`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### GET /auth/profile

Retrieve the authenticated user's full profile document.

**Auth required:** Yes — `Authorization: Bearer <access_token>`

#### Token Resolution (`search_user` dependency)

The request goes through a multi-step guard before the handler is called:

1. Extract the Bearer token from the `Authorization` header.
2. Decode and validate the JWT signature using `JWT_SECRET`.
3. Extract `sub` (email) from the decoded payload.
4. Query MongoDB for a user with that email.
5. Serialize `_id` (MongoDB ObjectId) to string and return the document.

#### Responses

| Status | Meaning |
|---|---|
| `200 OK` | User document returned. |
| `401 Unauthorized` | Token missing, malformed, or expired. |
| `404 Not Found` | Valid token but user no longer exists in DB. |

#### Example Request + Response

<details>
<summary><strong>cURL</strong></summary>

```bash
curl -X GET http://localhost:8000/api/auth/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```
</details>

<details>
<summary><strong>JavaScript (fetch)</strong></summary>

```javascript
const accessToken = localStorage.getItem("access_token");

const response = await fetch("http://localhost:8000/api/auth/profile", {
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
});

if (response.status === 401) {
  // Token expired — try refreshing
  await refreshTokens();
}

const user = await response.json();
console.log(user.email, user.profile);
```
</details>

<details>
<summary><strong>Python (httpx)</strong></summary>

```python
import httpx

access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

r = httpx.get(
    "http://localhost:8000/api/auth/profile",
    headers={"Authorization": f"Bearer {access_token}"},
)
r.raise_for_status()
user = r.json()
print(user["email"], user["profile"])
```
</details>

**Success Response `200`:**
```json
{
  "_id": "6642f1abc1234567890abcde",
  "email": "alice@example.com",
  "profile": {
    "age": 28,
    "gender": "female",
    "occupation": "Software Engineer",
    "sleep_hours": 7.5,
    "social_support": "moderate",
    "life_events": ["changed jobs", "relocated"]
  },
  "created_at": "2025-01-15T09:30:00.000000",
  "refresh_tokens": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
}
```

**Error Response `401`:**
```json
{
  "detail": "Invalid or expired token"
}
```

---

### POST /auth/refresh

Exchange a valid refresh token for a new access token.

**Accepts:** `application/json`  
**Auth required:** No (the refresh token itself is the credential)

#### Request Body

| Field | Type | Required | Description |
|---|---|---|---|
| `refresh_token` | string | ✅ | Previously issued, non-revoked JWT refresh token |

#### Server-side Validation

The endpoint performs these checks **in order** before issuing a new token:

1. JWT signature valid (HS256 + `JWT_SECRET`)
2. Token not expired (`exp` claim)
3. `sub` (email) exists in payload
4. User with that email exists in MongoDB
5. Token is present in `user.refresh_tokens[]` (not revoked by logout)

#### Responses

| Status | Meaning |
|---|---|
| `200 OK` | New access token issued. Refresh token unchanged. |
| `401 Unauthorized` | Token invalid, expired, or revoked. |
| `422 Unprocessable Entity` | Schema validation failed. |

#### Example Request + Response

<details>
<summary><strong>cURL</strong></summary>

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```
</details>

<details>
<summary><strong>JavaScript (fetch)</strong></summary>

```javascript
async function refreshTokens() {
  const refreshToken = localStorage.getItem("refresh_token");

  const response = await fetch("http://localhost:8000/api/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    // Refresh token expired or revoked — redirect to login
    window.location.href = "/login";
    return;
  }

  const { access_token } = await response.json();
  localStorage.setItem("access_token", access_token);
  return access_token;
}
```
</details>

<details>
<summary><strong>Python (httpx)</strong></summary>

```python
import httpx

r = httpx.post(
    "http://localhost:8000/api/auth/refresh",
    json={"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
)
r.raise_for_status()
new_access_token = r.json()["access_token"]
```
</details>

**Success Response `200`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.NEW_TOKEN...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Response `401`:**
```json
{
  "detail": "Invalid or expired refresh token"
}
```

---

### GET /auth/logout

Invalidate all active sessions for the authenticated user.

**Auth required:** Yes — `Authorization: Bearer <access_token>`

#### Behavior

- Identifies the user via the JWT access token in the `Authorization` header.
- Clears the entire `refresh_tokens[]` array in MongoDB.
- **Effect:** All previously issued refresh tokens become permanently invalid, across **all devices or sessions**.
- The current access token continues to work until its own TTL expires (default: 1 minute). For stricter invalidation, implement an access token blocklist.

#### Responses

| Status | Meaning |
|---|---|
| `200 OK` | Logged out. Refresh tokens cleared. |
| `200 OK` (already out) | No refresh tokens existed; user was already logged out. |
| `401 Unauthorized` | Access token missing, invalid, or expired. |
| `404 Not Found` | User matching the token not found (rare edge case). |

#### Example Request + Response

<details>
<summary><strong>cURL</strong></summary>

```bash
curl -X GET http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```
</details>

<details>
<summary><strong>JavaScript (fetch)</strong></summary>

```javascript
const accessToken = localStorage.getItem("access_token");

await fetch("http://localhost:8000/api/auth/logout", {
  headers: { Authorization: `Bearer ${accessToken}` },
});

// Clear local tokens regardless of server response
localStorage.removeItem("access_token");
localStorage.removeItem("refresh_token");
```
</details>

<details>
<summary><strong>Python (httpx)</strong></summary>

```python
import httpx

r = httpx.get(
    "http://localhost:8000/api/auth/logout",
    headers={"Authorization": f"Bearer {access_token}"},
)
print(r.json()["message"])
```
</details>

**Success Response `200` (normal logout):**
```json
{
  "message": "Token deletion True. You have successfully logged out"
}
```

**Success Response `200` (already logged out):**
```json
{
  "message": "Token deletion Already logged out. You have successfully logged out"
}
```

**Error Response `404` (no active session):**
```json
{
  "message": "You are not logged in"
}
```

---

## Data Schemas

### UserCreate (request)

```json
{
  "email": "alice@example.com",
  "password": "S3cur3P@ssw0rd"
}
```

| Field | Type | Constraints |
|---|---|---|
| `email` | `string` (email format) | Required, unique |
| `password` | `string` | Required, 8–72 chars |

---

### UserLogin (request)

```json
{
  "email": "alice@example.com",
  "password": "S3cur3P@ssw0rd"
}
```

---

### RefreshRequest (request)

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### TokenResponse (response)

Returned by `/register`, `/login`, `/refresh`, and `/login/swagger`.

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

> **Note:** `/register` and `/login` wrap this in `{ "message": "...", "content": { ...TokenResponse } }`.

---

### UserResponse (response — profile)

Full MongoDB user document returned by `GET /auth/profile`.

```json
{
  "_id": "6642f1abc1234567890abcde",
  "email": "alice@example.com",
  "profile": {
    "age": 28,
    "gender": "female",
    "occupation": "Software Engineer",
    "sleep_hours": 7.5,
    "social_support": "moderate",
    "life_events": ["changed jobs", "relocated"]
  },
  "created_at": "2025-01-15T09:30:00.000000",
  "refresh_tokens": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
}
```

#### UserProfile object fields

| Field | Type | Default | Description |
|---|---|---|---|
| `age` | integer \| null | `null` | User's age |
| `gender` | string \| null | `null` | User's gender identity |
| `occupation` | string \| null | `null` | Current occupation |
| `sleep_hours` | number \| null | `null` | Average nightly sleep hours |
| `social_support` | string \| null | `null` | Perceived social support level |
| `life_events` | string[] | `[]` | Self-reported major life events |

---

## Error Reference

All errors follow FastAPI's standard error envelope:

```json
{ "detail": "<human-readable message>" }
```

Validation errors return an array under `detail`:

```json
{
  "detail": [
    { "loc": ["body", "field_name"], "msg": "...", "type": "..." }
  ]
}
```

### HTTP Status Code Summary

| Code | Trigger | Example message |
|---|---|---|
| `201 Created` | Registration succeeded | — |
| `200 OK` | Request succeeded | — |
| `401 Unauthorized` | Invalid/expired/missing token or wrong credentials | `"Invalid or expired token"` |
| `404 Not Found` | User lookup failed post-authentication | `"Please login first"` |
| `409 Conflict` | Email already registered | `"User already exists"` |
| `422 Unprocessable Entity` | Pydantic schema validation failed | *(array of field errors)* |

---

## Token Lifecycle

### Detailed sequence diagram

```
Client                          API Server                  MongoDB
  │                                 │                          │
  │──POST /auth/register ──────────►│                          │
  │  { email, password }            │──find_one(email) ───────►│
  │                                 │◄── null (not found) ─────│
  │                                 │──bcrypt hash password    │
  │                                 │──insert_one(user doc) ──►│
  │                                 │──create_access_token()   │
  │                                 │──create_refresh_token()  │
  │                                 │──$push refresh_tokens ──►│
  │◄── 201 { access, refresh } ─────│                          │
  │                                 │                          │
  │──GET /auth/profile ─────────────►│                         │
  │  Authorization: Bearer <access> │──decode_token()          │
  │                                 │──find_one(email) ───────►│
  │◄── 200 { user document } ────────│◄── user doc ────────────│
  │                                 │                          │
  │  (access token expires)         │                          │
  │                                 │                          │
  │──POST /auth/refresh ────────────►│                         │
  │  { refresh_token }              │──decode_token()          │
  │                                 │──find_one(email) ───────►│
  │                                 │──check refresh_tokens[] ►│
  │                                 │──create_access_token()   │
  │◄── 200 { new_access, refresh } ──│                         │
  │                                 │                          │
  │──GET /auth/logout ──────────────►│                         │
  │  Authorization: Bearer <access> │──decode_token()          │
  │                                 │──$set refresh_tokens: []►│
  │◄── 200 { message: "logged out" }─│                         │
```

### Multi-session behavior

- Each login appends a new refresh token to `refresh_tokens[]` — multiple active sessions are supported.
- `GET /auth/logout` clears the **entire** array, terminating all sessions simultaneously.
- Individual session revocation (logout from one device only) is not yet implemented.

---

## Endpoint Summary

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | No | Register a new user; returns token pair |
| `POST` | `/api/auth/login` | No | Authenticate user; returns token pair |
| `POST` | `/api/auth/login/swagger` | No | Swagger UI OAuth2 login (form-data) |
| `GET` | `/api/auth/profile` | ✅ Bearer | Get authenticated user's full profile |
| `POST` | `/api/auth/refresh` | No | Exchange refresh token for new access token |
| `GET` | `/api/auth/logout` | ✅ Bearer | Revoke all refresh tokens (logout all sessions) |
