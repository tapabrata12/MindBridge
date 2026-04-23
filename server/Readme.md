# MindBridge

MindBridge is an AI-powered mental wellness companion backend. The product goal is to guide users through secure onboarding, profile-based personalization, structured mental wellness screening, supportive insight generation, crisis safety handling, referral discovery, and follow-up workflows.

This repository currently contains the backend service only. The frontend, assessment engine, LangGraph orchestration, RAG pipeline, crisis service, clinic finder, reporting, notifications, and feedback workflows are still planned modules.

Last verified against backend code: April 23, 2026.

## Current Repository Status

Implemented in this backend:

- FastAPI application with startup/shutdown lifespan hooks
- MongoDB connection management using Motor
- Health and root status endpoints
- Self-hosted JWT authentication
- bcrypt password hashing through Passlib
- User registration and login
- Swagger-compatible login endpoint
- Authenticated `/auth/me` endpoint
- Refresh-token rotation
- Logout by clearing all active refresh tokens for the user
- Profile read and update endpoints under `/api/profile`
- Strict Pydantic v2 request/response schemas
- Environment-driven configuration through Pydantic settings

Not implemented yet:

- Frontend app
- Assessment engine routes/services
- LangGraph state orchestration
- ChromaDB/RAG pipeline
- LLM integration
- Crisis detection service
- Report generator
- Clinic finder
- Notifications and follow-up system
- Automated test suite

## Current Architecture

```mermaid
flowchart LR
    CLIENT[Client / Swagger UI] --> APP[FastAPI App]
    APP --> AUTH[/api/auth routes]
    APP --> PROFILE[/api/profile routes]
    AUTH --> USER_SERVICE[User Service]
    PROFILE --> USER_SERVICE
    USER_SERVICE --> SECURITY[JWT + bcrypt]
    USER_SERVICE --> MONGO[(MongoDB)]
```

The current backend is still foundation-level: authentication, session control, and user profile management are in place. The AI wellness workflow is still defined in planning documents, not code.

## Project Structure

```text
server/
|-- src/
|   |-- api/
|   |   |-- __init__.py
|   |   `-- routes/
|   |       |-- auth.py
|   |       `-- profile.py
|   |-- core/
|   |   |-- config.py
|   |   |-- dependencies.py
|   |   `-- security.py
|   |-- db/
|   |   `-- mongodb.py
|   |-- models/
|   |   `-- user.py
|   |-- schemas/
|   |   `-- user.py
|   |-- services/
|   |   `-- user_service.py
|   `-- main.py
|-- API-DOCUMENTATION.md
|-- pyproject.toml
|-- uv.lock
`-- Readme.md
```

## Key Files

- `src/main.py` creates the FastAPI app, mounts routers, and exposes `/` and `/health`.
- `src/api/routes/auth.py` exposes register, login, Swagger login, current-user, refresh, and logout endpoints.
- `src/api/routes/profile.py` exposes profile read and update endpoints.
- `src/core/config.py` validates environment variables and normalizes API settings.
- `src/core/dependencies.py` resolves the authenticated user from a Bearer access token.
- `src/core/security.py` handles password hashing plus JWT creation/decoding.
- `src/db/mongodb.py` manages the async MongoDB client lifecycle.
- `src/models/user.py` defines the MongoDB user document shape.
- `src/schemas/user.py` defines Pydantic request/response schemas.
- `src/services/user_service.py` contains auth, token, logout, and profile database operations.

## Getting Started

### Prerequisites

- Python `3.14`
- `uv`
- MongoDB Atlas or a local MongoDB instance

### Install Dependencies

```powershell
cd D:\Mental-Helth-Companion\server
uv sync
```

### Run The API

```powershell
uv run uvicorn src.main:app --reload
```

Default local URLs:

- Root: `http://localhost:8000/`
- Health: `http://localhost:8000/health`
- API base: `http://localhost:8000/api`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

The backend reads environment variables from `server/.env`.

| Variable | Required | Default | Notes |
|---|---:|---|---|
| `PREFIX` | Yes | none | API prefix. The code normalizes it to start with `/` and removes trailing `/`. |
| `MONGODB_URL` | Yes | none | MongoDB connection string. |
| `DATABASE_NAME` | Yes | none | MongoDB database name. |
| `USER_COLLECTION` | Yes | none | MongoDB collection for user documents. |
| `JWT_SECRET` | Yes | none | Must be at least 32 characters. |
| `JWT_ALGORITHM` | No | `HS256` | Allowed values: `HS256`, `HS384`, `HS512`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Must be between `1` and `1440`. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Must be between `1` and `90`. |

Example:

```dotenv
PREFIX=/api
MONGODB_URL=mongodb+srv://<username>:<password>@<cluster>/<database>?retryWrites=true&w=majority
DATABASE_NAME=mindbridge
USER_COLLECTION=users
JWT_SECRET=<use-a-random-secret-at-least-32-characters-long>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Do not commit real secrets.

## API Overview

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | No | Service status message. |
| `GET` | `/health` | No | Health check response. |
| `POST` | `/api/auth/register` | No | Create a user and return an access/refresh token pair. |
| `POST` | `/api/auth/login` | No | Authenticate a user and return an access/refresh token pair. |
| `POST` | `/api/auth/login/swagger` | No | OAuth2 form login used by Swagger UI. |
| `GET` | `/api/auth/me` | Yes | Return the authenticated user's email. |
| `POST` | `/api/auth/refresh` | No | Rotate refresh token and issue a new token pair. |
| `POST` | `/api/auth/logout` | Yes | Clear all refresh tokens for the authenticated user. |
| `GET` | `/api/profile` | Yes | Return the authenticated user's profile. |
| `PUT` | `/api/profile` | Yes | Replace the authenticated user's stored profile with validated profile data. |

Full endpoint details are in `API-DOCUMENTATION.md`.

## Authentication And Sessions

The backend uses JWT Bearer authentication:

- Access tokens include `sub`, `exp`, `type`, and `iat` claims.
- Refresh tokens include the same core claims and are stored server-side in `refresh_tokens`.
- Register and login append a refresh token to the user's `refresh_tokens` array.
- Refresh validates the submitted refresh token, removes it from `refresh_tokens`, creates a new refresh token, stores the new one, and returns a new token pair.
- Logout clears the entire `refresh_tokens` array, invalidating all sessions for that user.
- Protected routes require a valid access token and at least one active refresh token in the user's document.

Because protected routes check that `refresh_tokens` is not empty, logout effectively invalidates access to protected routes immediately, even if the access token has not reached its `exp` time yet.

## User Document Shape

New users are created with this MongoDB document structure:

```json
{
  "email": "alice@example.com",
  "hash_password": "<bcrypt-hash>",
  "profile": {
    "age": null,
    "gender": null,
    "occupation": null,
    "sleep_hours": null,
    "social_support": null,
    "life_events": []
  },
  "refresh_tokens": [],
  "session": {
    "last_login_at": null,
    "last_password_change_at": null,
    "failed_login_attempts": 0,
    "is_locked": false
  },
  "roles": ["user"],
  "is_active": true,
  "created_at": "<utc-iso-timestamp>",
  "updated_at": "<utc-iso-timestamp>"
}
```

Note: `last_login_at`, failed login counters, account lock behavior, roles, and `is_active` are stored in the model but are not actively enforced by routes yet.

## Profile Fields

The implemented profile schema currently supports:

| Field | Type | Allowed values / range |
|---|---|---|
| `age` | integer or null | `10` to `100` |
| `gender` | string or null | `male`, `female`, `other` |
| `occupation` | string or null | `student`, `working`, `unemployed`, `retired`, `other` |
| `sleep_hours` | integer or null | `0` to `24` |
| `social_support` | string or null | `high`, `medium`, `low` |
| `life_events` | string array | Cleaned, empty strings removed, max 5 items |

Current `PUT /api/profile` behavior replaces the stored `profile` object with the validated schema output. If a field is omitted, it is saved as `null` or `[]` based on the schema default. It is not currently a partial patch operation.

## Delivery Workflow

The broader project roadmap remains:

| Workstream | Scope | Current status |
|---|---|---|
| `01 - JWT Auth` | Signup, login, refresh, current-user endpoint | Implemented baseline |
| `02 - User Profiles` | Profile schemas, service, read/update routes | Implemented baseline |
| `03 - Assessment Engine` | LangGraph flow and PHQ-9 screener | Not started |
| `04 - RAG Pipeline` | ChromaDB setup and document ingestion | Not started |
| `05 - Crisis Safety Net` | Detection middleware and helpline response | Not started |
| `06 - Report Generator` | Insight report and coping plan output | Not started |
| `07 - Frontend Auth` | Login/signup UI and token handling | Not started |
| `08 - Frontend Chat UI` | Streaming chat interface | Not started |
| `09 - Clinic Finder` | Google Maps integration | Not started |
| `10 - Testing` | Backend and frontend tests | Not started |

## Planned Target Stack

| Area | Decision |
|---|---|
| Frontend | React + Tailwind + shadcn/ui |
| Backend | FastAPI + Uvicorn |
| Auth | Self-hosted JWT + bcrypt |
| Database | MongoDB Atlas |
| Vector store | ChromaDB |
| Embeddings | `nomic-embed-text` |
| Orchestration | LangGraph |
| LLM | GPT-4o-mini or Gemini Flash |
| Maps | Google Maps Places API |
| Notifications | Email / WhatsApp |
| Hosting | Railway backend + Vercel frontend |

## Security And Safety Notes

- Passwords are stored only as bcrypt hashes.
- JWT secrets must be managed through environment variables.
- Refresh tokens are revocable because they are stored server-side.
- Logout revokes all active refresh tokens for the user.
- The app must remain positioned as wellness support and screening, not diagnosis.
- Crisis detection is mandatory before conversational assessment/chat features are added.

## Verification

Syntax verification command:

```powershell
.\.venv\Scripts\python.exe -m compileall src
```

Route table check command:

```powershell
@'
from src.main import app
for route in app.routes:
    methods = ",".join(sorted(route.methods or []))
    print(methods, route.path)
'@ | .\.venv\Scripts\python.exe -
```
