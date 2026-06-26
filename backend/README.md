# AI Software Architect — Backend (Auth Module)

FastAPI + SQLAlchemy (async) + PostgreSQL authentication service.

## Stack
FastAPI · SQLAlchemy 2 (async) + Alembic · PostgreSQL · Pydantic · Argon2 ·
JWT (python-jose) · Google OAuth (google-auth) · slowapi · fastapi-mail.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on *nix)
pip install -r requirements.txt # or: pip install -e ".[dev]"
copy .env.example .env          # cp .env.example .env on *nix
# Edit .env: set DATABASE_URL, ACCESS/REFRESH secrets, GOOGLE_CLIENT_ID, SMTP...
```

Generate strong secrets:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## Database / migrations

```bash
alembic revision --autogenerate -m "init auth"
alembic upgrade head
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- ReDoc:      http://localhost:8000/redoc
- Health:     http://localhost:8000/health

## Tests

```bash
pytest
```

## Architecture

```
routes -> controllers -> services -> repositories -> DB
```

- **controllers/** HTTP only (parse, set cookies, status codes)
- **services/** business logic (no HTTP/DB specifics)
- **repositories/** the only layer touching the DB
- **validators/** Pydantic request schemas (server-side validation)
- **dto/** response models (ORM never leaves the boundary)
- **utils/** token hashing, domain exceptions
- **core/** settings, security deps, rate limit, middleware

## Security notes

- Argon2id hashing; passwords never stored/logged/returned.
- Access JWT (~15m) + rotating refresh token (~7d), stored hashed, HTTP-only cookie.
- Refresh reuse => whole token family revoked (theft detection).
- CSRF double-submit token for cookie-based mutations.
- Rate limiting on login/register/forgot-password.
- Generic auth + forgot-password responses (no user enumeration).
- CORS locked to `CLIENT_ORIGIN`; security headers + HSTS in production.
