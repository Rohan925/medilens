# MediLens

MediLens is a full-stack medicine assistant that combines structured drug lookup, conversational Q&A, and OCR-based medicine recognition in one application.

The project has:
- A `FastAPI` backend for authentication, search, chat, OCR orchestration, and data access
- A `React + Vite` frontend for login, medicine lookup, chat, and camera/upload OCR flows
- A `PostgreSQL` database for user accounts
- External integrations with `OpenAI`, `OpenFDA`, and `PubChem`

## What It Does

MediLens supports three main user flows:

1. `Search`
Users can search for a medicine and receive a structured summary with uses, warnings, mechanism details, prescription status, and citations.

2. `Chat`
Users can ask medicine-related or general health questions. The backend routes the prompt through a graph-based workflow that can answer directly or retrieve medicine data first when needed.

3. `OCR`
Users can upload or capture an image of a medicine package/label. The backend extracts text, attempts to resolve the medicine, and returns a structured summary with citations.

All primary product routes are protected by session-based authentication.

## Tech Stack

### Backend
- `FastAPI`
- `Pydantic`
- `psycopg`
- `LangGraph`
- `langchain-openai`
- `python-dotenv`
- `requests`

### Frontend
- `React 19`
- `React Router`
- `Vite`
- `react-markdown`

### Infrastructure
- `PostgreSQL 15`
- `Docker Compose` for local database setup

## Project Structure

```text
medilens/
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   └── app/
│       ├── api/
│       │   ├── routes/
│       │   └── schemas/
│       ├── domain/
│       ├── graph/
│       ├── services/
│       └── tests/
├── frontend/
│   ├── package.json
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── css/
│       └── lib/
├── docker-compose.yml
└── README.md
```

## Architecture Summary

### Authentication
- Users register and log in through backend auth routes.
- Passwords are hashed with `PBKDF2-HMAC-SHA256`.
- Successful login sets an `HttpOnly` cookie.
- The cookie contains a signed token built from:
  - `sub`: user id
  - `exp`: session expiry timestamp
- The token is signed with `AUTH_SECRET`.

### Search and Chat
- Search and chat endpoints build a graph state and run a LangGraph workflow.
- Medicine data is enriched through:
  - `OpenFDA` for label and regulatory information
  - `PubChem` for compound metadata and descriptions
- OpenAI is used for text reasoning and response generation.

### OCR
- The frontend can upload an image or capture one from the device camera.
- The backend validates file type and size, stores a temporary image, and runs an OCR graph.
- OCR responses include:
  - medicine name
  - confidence score
  - structured summary
  - citations
  - fallback/error information when resolution is weak

## Quick Start

From the project root:

```bash
docker compose up -d
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open `http://127.0.0.1:5173`.

## Local Setup

### Prerequisites

Install these locally before starting:
- `Python 3.11+` recommended
- `Node.js 18+`
- `npm`
- `Docker` and `Docker Compose`

### 1. Start PostgreSQL

From the project root:

```bash
docker compose up -d
```

This starts a local PostgreSQL container with:
- database: `medilens_db`
- user: `medilens`
- password: `medilens123`
- port: `5432`

To stop it:

```bash
docker compose down
```

To stop it and remove database data:

```bash
docker compose down -v
```

### 2. Backend Setup

Create and activate a virtual environment:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the backend environment file:

```bash
cp .env.example .env
```

Update `backend/.env` with real values where needed.

### Backend environment variables

`backend/.env.example` currently defines:

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5-mini
OPENAI_VISION_MODEL=gpt-5-mini
DATABASE_URL=postgresql://medilens:medilens123@127.0.0.1:5432/medilens_db
AUTH_SECRET=replace-this-with-a-long-random-secret
FRONTEND_ORIGINS=http://127.0.0.1:5173
COOKIE_SECURE=false
```

What each variable does:
- `OPENAI_API_KEY`: required for chat and OCR model-backed flows
- `OPENAI_MODEL`: text model used by the backend
- `OPENAI_VISION_MODEL`: vision-capable model used for OCR/image interpretation
- `DATABASE_URL`: PostgreSQL connection string
- `AUTH_SECRET`: secret key used to sign and verify session cookies
- `FRONTEND_ORIGINS`: comma-separated list of frontend origins allowed by CORS
- `COOKIE_SECURE`: set to `true` only when serving over HTTPS

If `OPENAI_API_KEY` is missing, the backend can still start, but chat and OCR model-backed flows will not work correctly.

### Generate a secure `AUTH_SECRET`

Use a long random value, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Notes:
- Do not use the placeholder value in real deployments.
- Changing `AUTH_SECRET` invalidates all active sessions.

### Run the backend

From `backend/`:

```bash
uvicorn app.main:app --reload
```

Default backend URL:

```text
http://127.0.0.1:8000
```

On startup the backend initializes the `users` table automatically.

### 3. Frontend Setup

In a second terminal:

```bash
cd frontend
npm install
```

Run the dev server:

```bash
npm run dev
```

Default frontend URL:

```text
http://127.0.0.1:5173
```

### Frontend API base URL

The frontend uses:

- `VITE_API_BASE_URL` if provided
- otherwise `http://127.0.0.1:8000`

If you need a custom backend URL, create `frontend/.env` and set:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## First Run Checklist

1. Start Postgres with `docker compose up -d`
2. Create `backend/.env` from `backend/.env.example`
3. Add a valid `OPENAI_API_KEY`
4. Replace `AUTH_SECRET` with a random secret
5. Start the backend with `uvicorn app.main:app --reload`
6. Start the frontend with `npm run dev`
7. Open `http://127.0.0.1:5173`
8. Register a user and log in

## API Overview

Base URL: `http://127.0.0.1:8000`

### Auth
- `POST /register`
  - Creates a new user account
  - Password must be between `8` and `128` characters
- `POST /login`
  - Validates credentials and sets the auth cookie
- `GET /me`
  - Returns the currently authenticated user
- `POST /logout`
  - Clears the auth cookie

### Protected product routes
- `POST /search`
  - Request body: `{ "query": "ibuprofen" }`
- `POST /chat`
  - Request body: `{ "query": "...", "history": [...] }`
- `POST /ocr`
  - Multipart form upload with `file`
  - Accepted types: `jpeg`, `png`, `webp`
  - Maximum size: `5 MB`

## Authentication Notes

- Auth is cookie-based, not token-in-local-storage based.
- The cookie is `HttpOnly`, so frontend JavaScript does not read it directly.
- Protected frontend routes verify the session by calling `GET /me`.
- `COOKIE_SECURE=false` is correct for local `http://127.0.0.1` development.
- In production behind HTTPS, set `COOKIE_SECURE=true`.

## Running Tests

Backend tests live under `backend/app/tests/`.

Run them from `backend/`:

```bash
python -m unittest discover -s app/tests
```

If imports fail in your environment, run:

```bash
PYTHONPATH=. python -m unittest discover -s app/tests
```

Frontend linting:

```bash
cd frontend
npm run lint
```

## Common Development Notes

### Password validation
- Passwords shorter than 8 characters are rejected by backend schema validation.

### CORS issues
- Ensure the frontend URL is present in `FRONTEND_ORIGINS`.
- For multiple origins, use a comma-separated list.

Example:

```env
FRONTEND_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

### Database connection issues
- Make sure the Postgres container is running.
- Confirm `DATABASE_URL` matches the Compose credentials.
- Ensure nothing else is already using port `5432`.

### OpenAI-dependent features
- Chat and OCR flows depend on valid OpenAI credentials and model availability.
- Retrieval from OpenFDA and PubChem also depends on outbound network access.

## Current Behavior and Limitations

- The backend creates the `users` table automatically, but there is no full migration system yet.
- Auth uses a custom signed-cookie token format rather than JWT.
- Search/chat/OCR quality depends on external provider availability and model behavior.
- OCR accepts common image formats only and enforces a 5 MB size limit.

## Useful Commands

From project root:

```bash
docker compose up -d
docker compose down
```

From `backend/`:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
python -m unittest discover -s app/tests
```

From `frontend/`:

```bash
npm install
npm run dev
npm run build
npm run lint
```

## Suggested Next Improvements

- Add pinned backend dependency versions
- Add a proper migration tool such as Alembic
- Add backend auth and route integration tests
- Add API documentation examples for each endpoint
- Add deployment-specific environment documentation
