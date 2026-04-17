# Mental Health Companion — Backend API

> **Framework:** FastAPI · **Database:** MongoDB (Motor async) · **Auth:** JWT Bearer (HS256) · **Runtime:** Python ≥ 3.14 / Uvicorn

---

## OpenAPI 3.1 Specification

```yaml
openapi: "3.1.0"

info:
  title: Mental Health Companion API
  version: "1.0.0"
  description: |
    REST API for the **Mental Health Companion** platform (code-name *Mindbridge*).
    Handles user registration, authentication, token lifecycle management,
    and serves authenticated user profile data.

    ### Authentication
    The API uses **JWT Bearer tokens** signed with HS256.
    - **Access token** — short-lived (default 1 minute), sent in `Authorization: Bearer <token>` header.
    - **Refresh token** — long-lived (default 7 days), stored server-side in MongoDB and invalidated on logout.

    ### Base URL
    ```
    http://localhost:8000/api
    ```
  contact:
    name: Tapabrata Chowdhury
  license:
    name: MIT

servers:
  - url: http://localhost:8000/api
    description: Local development server

tags:
  - name: Authentication
    description: >
      Endpoints for user registration, login, token refresh, profile retrieval,
      and logout. All token-protected routes require a valid JWT access token
      in the `Authorization` header.

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: >
        JWT access token obtained from `/api/auth/register` or `/api/auth/login`.
        Include in every protected request as `Authorization: Bearer <access_token>`.

    OAuth2SwaggerFlow:
      type: oauth2
      description: >
        OAuth2 password flow **exclusively for Swagger UI** (`/docs`).
        Points to the `/api/auth/login/swagger` form-data endpoint.
      flows:
        password:
          tokenUrl: /api/auth/login/swagger
          scopes: {}

  schemas:
    # ─── Request Bodies ────────────────────────────────────────────────────────

    UserCreate:
      type: object
      required: [email, password]
      properties:
        email:
          type: string
          format: email
          example: alice@example.com
          description: A valid email address. Must be unique across all users.
        password:
          type: string
          minLength: 8
          maxLength: 72
          example: "S3cur3P@ssw0rd"
          description: >
            Plain-text password. Minimum 8 characters, maximum 72 characters
            (bcrypt hard limit). Stored as a bcrypt hash; never returned in responses.

    UserLogin:
      type: object
      required: [email, password]
      properties:
        email:
          type: string
          format: email
          example: alice@example.com
        password:
          type: string
          example: "S3cur3P@ssw0rd"

    RefreshRequest:
      type: object
      required: [refresh_token]
      properties:
        refresh_token:
          type: string
          example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
          description: >
            Valid, non-revoked refresh token previously issued by `/register` or `/login`.

    # ─── Response Bodies ───────────────────────────────────────────────────────

    TokenResponse:
      type: object
      properties:
        access_token:
          type: string
          example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZUBleGFtcGxlLmNvbSIsImV4cCI6MTcxMzM0MDAwMH0.abc123"
          description: Short-lived JWT access token (default expiry: 1 minute).
        refresh_token:
          type: string
          example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZUBleGFtcGxlLmNvbSIsImV4cCI6MTcxMzk0MDAwMH0.xyz789"
          description: Long-lived JWT refresh token (default expiry: 7 days). Stored server-side.
        token_type:
          type: string
          example: "bearer"
          default: "bearer"

    RegisterSuccessResponse:
      type: object
      properties:
        message:
          type: string
          example: "User successfully registered"
        content:
          $ref: "#/components/schemas/TokenResponse"

    LoginSuccessResponse:
      type: object
      properties:
        message:
          type: string
          example: "User successfully logged in"
        content:
          $ref: "#/components/schemas/TokenResponse"

    UserResponse:
      type: object
      description: Authenticated user's public profile data.
      properties:
        _id:
          type: string
          example: "6642f1abc1234567890abcde"
          description: MongoDB ObjectId serialized as string.
        email:
          type: string
          format: email
          example: alice@example.com
        profile:
          $ref: "#/components/schemas/UserProfile"
        created_at:
          type: string
          format: date-time
          example: "2025-01-15T09:30:00.000000"
        refresh_tokens:
          type: array
          items:
            type: string
          description: Array of active server-side refresh tokens (internal field, may be omitted in future versions).

    UserProfile:
      type: object
      description: Optional mental-health profile fields. All fields are `null` until explicitly set.
      properties:
        age:
          type: integer
          nullable: true
          example: 28
        gender:
          type: string
          nullable: true
          example: "female"
        occupation:
          type: string
          nullable: true
          example: "Software Engineer"
        sleep_hours:
          type: number
          nullable: true
          example: 7.5
          description: Average nightly sleep hours.
        social_support:
          type: string
          nullable: true
          example: "moderate"
          description: Perceived level of social support.
        life_events:
          type: array
          items:
            type: string
          example: ["changed jobs", "relocated"]
          description: List of major life events the user has reported.

    LogoutResponse:
      type: object
      properties:
        message:
          type: string
          example: "Token deletion True. You have successfully logged out"

    ErrorResponse:
      type: object
      properties:
        detail:
          type: string
          example: "Invalid or expired token"

  responses:
    Unauthorized:
      description: Missing, invalid, or expired JWT token.
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
          example:
            detail: "Invalid or expired token"

    NotFound:
      description: Resource not found.
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
          example:
            detail: "Please login first"

    Conflict:
      description: Resource already exists.
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
          example:
            detail: "User already exists"

    ValidationError:
      description: Request body failed schema validation.
      content:
        application/json:
          schema:
            type: object
            properties:
              detail:
                type: array
                items:
                  type: object
                  properties:
                    loc:
                      type: array
                      items:
                        type: string
                    msg:
                      type: string
                    type:
                      type: string
          example:
            detail:
              - loc: ["body", "password"]
                msg: "String should have at least 8 characters"
                type: "string_too_short"

# ─── Paths ──────────────────────────────────────────────────────────────────────

paths:

  /auth/register:
    post:
      operationId: register_user
      tags: [Authentication]
      summary: Register a new user account
      description: |
        Creates a new user account with the provided email and password.

        **Behavior:**
        - Checks for an existing account with the same email — returns `409` if found.
        - Hashes the password with bcrypt before storage.
        - Issues both an **access token** and a **refresh token** upon successful registration.
        - The refresh token is persisted server-side in the user's `refresh_tokens` array.

        No email verification step is required at this stage.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/UserCreate"
            example:
              email: alice@example.com
              password: "S3cur3P@ssw0rd"
      responses:
        "201":
          description: User created successfully. Returns access and refresh tokens.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/RegisterSuccessResponse"
              example:
                message: "User successfully registered"
                content:
                  access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                  refresh_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                  token_type: "bearer"
        "409":
          $ref: "#/components/responses/Conflict"
        "422":
          $ref: "#/components/responses/ValidationError"

  /auth/login:
    post:
      operationId: login_user
      tags: [Authentication]
      summary: Authenticate an existing user
      description: |
        Validates the user's email and password and issues a new token pair.

        **Behavior:**
        - Returns `401` if no account exists for the given email.
        - Returns `401` if the password does not match the stored bcrypt hash.
        - On success, a new refresh token is **appended** to the server-side `refresh_tokens` array
          (multiple active sessions are supported).
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/UserLogin"
            example:
              email: alice@example.com
              password: "S3cur3P@ssw0rd"
      responses:
        "200":
          description: Authentication successful. Returns access and refresh tokens.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/LoginSuccessResponse"
              example:
                message: "User successfully logged in"
                content:
                  access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                  refresh_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                  token_type: "bearer"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "422":
          $ref: "#/components/responses/ValidationError"

  /auth/login/swagger:
    post:
      operationId: login_user_swagger
      tags: [Authentication]
      summary: Swagger UI — OAuth2 password login
      description: |
        **For Swagger UI / interactive docs use only.**

        Accepts `application/x-www-form-urlencoded` (OAuth2 Password Grant format)
        so the Swagger UI **Authorize** button works. Internally calls the same
        authentication logic as `POST /auth/login`.

        > ⚠️ Do **not** use this endpoint in production client code.
        > Use `POST /auth/login` with a JSON body instead.
      requestBody:
        required: true
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required: [username, password]
              properties:
                username:
                  type: string
                  format: email
                  description: The user's email address (mapped to `username` per OAuth2 spec).
                  example: alice@example.com
                password:
                  type: string
                  example: "S3cur3P@ssw0rd"
      responses:
        "200":
          description: Authentication successful.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/TokenResponse"
              example:
                access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                refresh_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                token_type: "bearer"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "422":
          $ref: "#/components/responses/ValidationError"

  /auth/profile:
    get:
      operationId: get_user_profile
      tags: [Authentication]
      summary: Retrieve the authenticated user's profile
      description: |
        Returns the full user document for the currently authenticated user,
        resolved from the JWT access token in the `Authorization` header.

        **Token resolution flow (`search_user` dependency):**
        1. Extract Bearer token from `Authorization` header.
        2. Decode and verify the JWT signature using the server secret.
        3. Extract `sub` (email) from the token payload.
        4. Look up the user in MongoDB by email.
        5. Serialize `_id` (ObjectId) as a string and return the full user document.
      security:
        - BearerAuth: []
        - OAuth2SwaggerFlow: []
      responses:
        "200":
          description: Authenticated user document.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/UserResponse"
              example:
                _id: "6642f1abc1234567890abcde"
                email: alice@example.com
                profile:
                  age: 28
                  gender: "female"
                  occupation: "Software Engineer"
                  sleep_hours: 7.5
                  social_support: "moderate"
                  life_events: ["changed jobs"]
                created_at: "2025-01-15T09:30:00.000000"
                refresh_tokens: ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
        "401":
          $ref: "#/components/responses/Unauthorized"
        "404":
          $ref: "#/components/responses/NotFound"

  /auth/refresh:
    post:
      operationId: refresh_access_token
      tags: [Authentication]
      summary: Issue a new access token using a refresh token
      description: |
        Exchanges a valid, non-revoked refresh token for a new access token.
        The refresh token itself is **not rotated** — the same refresh token is
        returned alongside the newly issued access token.

        **Validation steps:**
        1. Decode the refresh token and verify the HS256 signature.
        2. Extract `sub` (email) from the token payload.
        3. Confirm the user exists in MongoDB.
        4. Confirm the token is present in the user's `refresh_tokens` array
           (server-side revocation check — protects against reuse after logout).
        5. Issue and return a new access token.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RefreshRequest"
            example:
              refresh_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      responses:
        "200":
          description: New access token issued successfully.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/TokenResponse"
              example:
                access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.NEW..."
                refresh_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                token_type: "bearer"
        "401":
          description: Refresh token is invalid, expired, or has been revoked.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"
              example:
                detail: "Invalid or expired refresh token"
        "422":
          $ref: "#/components/responses/ValidationError"

  /auth/logout:
    get:
      operationId: logout_user
      tags: [Authentication]
      summary: Invalidate all refresh tokens for the authenticated user
      description: |
        Logs the user out by clearing the `refresh_tokens` array in MongoDB.
        This **revokes all active sessions** across all devices for this user.

        The access token passed in the `Authorization` header is used to
        identify the user (via the `search_user` dependency). After logout,
        any attempt to use existing refresh tokens — even unexpired ones — will fail.

        > **Note:** The short-lived access token itself is not blocklisted.
        > It continues to function until its natural expiry (default: 1 minute).
        > For production, consider implementing an access token blocklist if
        > immediate invalidation is required.
      security:
        - BearerAuth: []
        - OAuth2SwaggerFlow: []
      responses:
        "200":
          description: Successfully logged out. All refresh tokens cleared.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/LogoutResponse"
              examples:
                success:
                  summary: Normal logout
                  value:
                    message: "Token deletion True. You have successfully logged out"
                already_logged_out:
                  summary: Already logged out (no active tokens)
                  value:
                    message: "Token deletion Already logged out. You have successfully logged out"
        "401":
          $ref: "#/components/responses/Unauthorized"
        "404":
          description: User not found or already logged out.
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
              example:
                message: "You are not logged in"
```

---

## Quick Start

### Prerequisites

| Tool | Version |
|------|---------|
| Python | ≥ 3.14 |
| [uv](https://docs.astral.sh/uv/) | latest |
| MongoDB Atlas (or local) | any |

### Install & Run

```bash
# Clone and enter the server directory
cd server

# Install dependencies using uv
uv sync

# Copy and configure environment variables
cp .env.example .env   # then fill in MONGODB_URL, JWT_SECRET, etc.

# Start the development server
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive docs (Swagger UI) at `http://localhost:8000/docs`.

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PREFIX` | ✅ | — | Global route prefix (e.g. `/api`) |
| `MONGODB_URL` | ✅ | — | MongoDB connection string |
| `DATABASE_NAME` | ✅ | — | MongoDB database name |
| `USER_COLLECTION` | ✅ | — | Collection name for users |
| `JWT_SECRET` | ✅ | — | Secret key for signing JWTs |
| `JWT_ALGORITHM` | ❌ | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `1` | Access token TTL in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | ❌ | `7` | Refresh token TTL in days |

---

## Project Structure

```
server/
├── src/
│   ├── main.py                  # FastAPI app factory & lifespan hooks
│   ├── api/
│   │   └── routes/
│   │       └── auth.py          # Authentication router (all /auth/* endpoints)
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (reads from .env)
│   │   ├── security.py          # JWT encode/decode, bcrypt hashing
│   │   └── dependencies.py      # FastAPI dependency: search_user (token guard)
│   ├── db/
│   │   └── mongodb.py           # Motor async MongoDB client & lifecycle
│   ├── models/
│   │   └── user.py              # Document factory: create_user()
│   ├── schemas/
│   │   └── user.py              # Pydantic I/O schemas (request & response)
│   └── services/
│       └── user_service.py      # Business logic: register, login, refresh, logout
├── pyproject.toml
├── uv.lock
└── .env
```
