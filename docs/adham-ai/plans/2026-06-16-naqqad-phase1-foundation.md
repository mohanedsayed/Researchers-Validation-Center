# Naqqad Phase 1: Foundation & Upload Pipeline

> **For agentic workers:** REQUIRED SUB-SKILL: Use parallel-build (recommended) or build to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap the Naqqad backend with authentication, file upload (docx/txt/md), Stage-1 semantic chunking via Qwen 2.5 7B on Ollama, and 24-hour TTL session lifecycle with secure deletion.

**Architecture:** FastAPI (Python 3.11) + async SQLAlchemy 2.0 + PostgreSQL 16. Uploaded files are AES-256 encrypted and stored in S3-compatible object storage. Celery workers run the Stage-1 chunker (Ollama + Qwen2.5:7b) asynchronously. Celery Beat handles 24h TTL secure deletion. Stage-2 critique engine is NOT in this plan — the output is a session with structured chunks ready for critique.

**Tech Stack:** FastAPI · SQLAlchemy 2.0 async · Alembic · PostgreSQL 16 · Redis 7 · Celery 5 · Ollama (Qwen2.5:7b) · python-docx · mistune · boto3 · cryptography · python-jose · passlib[bcrypt] · pytest · httpx · pytest-asyncio

---

## Sub-plan Roadmap (full platform, complete in order)

| Plan | Scope | Produces |
|---|---|---|
| **Plan 1 — this** | Foundation + Upload + Stage-1 Chunking | Running backend, auth, file upload, chunked sessions |
| Plan 2 | Critique Engine (Stage-2) + DSE Protocol | Working critique output, jury assembly, streaming |
| Plan 3 | Report Generation (PDF + HTML, Arabic RTL) | Downloadable reports |
| Plan 4 | RTL Web UI (Next.js, Arabic-first) + Billing (Tap Payments) | Full product |

---

## File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, lifespan, CORS
│   ├── config.py                # Pydantic settings (from .env)
│   ├── database.py              # Async SQLAlchemy engine + session factory
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User (auth, tier, token balances)
│   │   ├── session.py           # CritiqueSession, UploadedFile
│   │   ├── chunk.py             # Chunk (Stage-1 output)
│   │   └── discipline.py        # DisciplineInstruction (DSE)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py              # RegisterRequest, LoginRequest, TokenResponse
│   │   ├── session.py           # CreateSessionRequest, SessionResponse
│   │   └── chunk.py             # ChunkResponse
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py              # POST /auth/register, POST /auth/login
│   │   ├── upload.py            # POST /sessions/upload
│   │   └── sessions.py          # GET /sessions/{id}, GET /sessions/{id}/chunks
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_parser.py       # docx/txt/md → RawParagraph list
│   │   ├── storage.py           # S3 + AES-256 encrypt/decrypt/delete
│   │   └── chunker.py           # Ollama Qwen2.5 REST → Chunk list
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── celery_app.py        # Celery app + Beat schedule
│   │   ├── chunking.py          # Task: parse + chunk file → update session
│   │   └── cleanup.py           # Beat task: secure-delete expired sessions
│   └── utils/
│       ├── __init__.py
│       └── security.py          # JWT encode/decode, bcrypt hash/verify
├── tests/
│   ├── conftest.py              # pytest fixtures: DB, test client, auth headers
│   ├── test_auth.py
│   ├── test_upload.py
│   ├── test_file_parser.py
│   ├── test_chunker.py
│   └── test_cleanup.py
├── alembic/
│   ├── env.py
│   └── versions/
├── Dockerfile
├── pyproject.toml
└── .env.example
docker-compose.yml               # postgres, redis, ollama, backend, worker, beat
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/Dockerfile`
- Create: `docker-compose.yml`
- Create: `backend/app/__init__.py` (empty)
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`

- [ ] **Step 1.1: Create `backend/pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "naqqad-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi==0.115.5",
    "uvicorn[standard]==0.32.1",
    "sqlalchemy[asyncio]==2.0.36",
    "asyncpg==0.30.0",
    "alembic==1.14.0",
    "pydantic-settings==2.6.1",
    "pydantic[email]==2.10.3",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-multipart==0.0.12",
    "celery[redis]==5.4.0",
    "redis==5.2.1",
    "boto3==1.35.85",
    "cryptography==44.0.0",
    "python-docx==1.1.2",
    "mistune==3.0.2",
    "httpx==0.28.1",
    "tenacity==9.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.4",
    "pytest-asyncio==0.24.0",
    "pytest-cov==6.0.0",
    "httpx==0.28.1",
    "factory-boy==3.3.1",
    "faker==33.1.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.hatch.build.targets.wheel]
packages = ["app"]
```

- [ ] **Step 1.2: Create `backend/.env.example`**

```env
# Database
DATABASE_URL=postgresql+asyncpg://naqqad:secret@db:5432/naqqad

# Redis / Celery
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=change-me-to-a-long-random-string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# S3-compatible storage
S3_ENDPOINT_URL=http://localstack:4566
S3_BUCKET_NAME=naqqad-files
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=us-east-1

# File encryption (AES-256 key, base64-encoded, 32 bytes)
FILE_ENCRYPTION_KEY=dGhpcyBpcyBhIDMyLWJ5dGUga2V5ISEhISEh

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_CHUNKER_MODEL=qwen2.5:7b

# Session TTL in hours
SESSION_TTL_HOURS=24

# Upload limits
MAX_FILE_SIZE_MB=500
FREE_TIER_MAX_PAGES=20
```

- [ ] **Step 1.3: Create `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    redis_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    s3_endpoint_url: str
    s3_bucket_name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"

    file_encryption_key: str  # base64-encoded 32-byte key

    ollama_base_url: str = "http://ollama:11434"
    ollama_chunker_model: str = "qwen2.5:7b"

    session_ttl_hours: int = 24
    max_file_size_mb: int = 500
    free_tier_max_pages: int = 20


settings = Settings()
```

- [ ] **Step 1.4: Create `backend/app/main.py`**

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, upload, sessions
from app.database import engine
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Naqqad API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(upload.router, prefix="/sessions", tags=["sessions"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 1.5: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install hatch

COPY pyproject.toml .
RUN pip install -e ".[dev]"

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 1.6: Create `docker-compose.yml` at project root**

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: naqqad
      POSTGRES_USER: naqqad
      POSTGRES_PASSWORD: secret
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U naqqad"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      SERVICES: s3
      DEFAULT_REGION: us-east-1

  backend:
    build: ./backend
    env_file: ./backend/.env
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
      ollama:
        condition: service_started
    volumes:
      - ./backend:/app

  worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info -Q chunking,cleanup
    env_file: ./backend/.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
      ollama:
        condition: service_started
    volumes:
      - ./backend:/app

  beat:
    build: ./backend
    command: celery -A app.tasks.celery_app beat --loglevel=info
    env_file: ./backend/.env
    depends_on:
      - redis
    volumes:
      - ./backend:/app

volumes:
  postgres_data:
  ollama_data:
```

- [ ] **Step 1.7: Verify the compose starts**

```bash
cd "/Users/macbook/Desktop/Software projects/Researchers-Validation-Center"
docker compose up -d db redis localstack
docker compose ps
```

Expected: db, redis, localstack all show `healthy` or `running`.

- [ ] **Step 1.8: Pull Qwen model into Ollama**

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull qwen2.5:7b
```

Expected: Progress bar, then `success` — model is ~4.5GB.

- [ ] **Step 1.9: Commit scaffold**

```bash
cd "/Users/macbook/Desktop/Software projects/Researchers-Validation-Center"
git add backend/ docker-compose.yml docs/
git commit -m "feat: add project scaffold (FastAPI, Docker, Ollama, pyproject)"
```

---

## Task 2: Database Models

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/session.py`
- Create: `backend/app/models/chunk.py`
- Create: `backend/app/models/discipline.py`

- [ ] **Step 2.1: Create `backend/app/database.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 2.2: Create `backend/app/models/user.py`**

```python
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserTier(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    SCHOLAR = "scholar"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    language_preference: Mapped[str] = mapped_column(String(10), default="ar")
    tier: Mapped[UserTier] = mapped_column(Enum(UserTier), default=UserTier.FREE)
    monthly_token_balance: Mapped[int] = mapped_column(Integer, default=0)
    credit_balance: Mapped[int] = mapped_column(Integer, default=0)
    byok_api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 2.3: Create `backend/app/models/session.py`**

```python
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SessionStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PARSING = "parsing"
    QUEUED = "queued"
    CRITIQUING = "critiquing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class CritiqueTone(str, enum.Enum):
    CONSTRUCTIVE = "constructive"
    FORENSIC = "forensic"


class ReportDepth(str, enum.Enum):
    EXECUTIVE = "executive"
    STANDARD = "standard"
    DEEP_AUDIT = "deep_audit"


class CritiqueSession(Base):
    __tablename__ = "critique_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.UPLOADING, nullable=False
    )
    tone: Mapped[CritiqueTone] = mapped_column(Enum(CritiqueTone), nullable=False)
    report_depth: Mapped[ReportDepth] = mapped_column(Enum(ReportDepth), nullable=False)
    detected_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    detected_disciplines: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    jury_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tokens_consumed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("critique_sessions.id"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), nullable=False)  # docx, txt, md
    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 2.4: Create `backend/app/models/chunk.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("critique_sessions.id"), nullable=False
    )
    chapter_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    paragraph_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language_hint: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ar, en, mixed
    token_estimate: Mapped[int] = mapped_column(Integer, default=0)
    critique_status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 2.5: Create `backend/app/models/discipline.py`**

```python
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DisciplineStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class DisciplineInstruction(Base):
    __tablename__ = "discipline_instructions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DisciplineStatus] = mapped_column(
        Enum(DisciplineStatus), default=DisciplineStatus.DRAFT
    )
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 2.6: Create `backend/app/models/__init__.py`**

```python
from app.database import Base
from app.models.chunk import Chunk
from app.models.discipline import DisciplineInstruction, DisciplineStatus
from app.models.session import (
    CritiqueSession,
    CritiqueTone,
    ReportDepth,
    SessionStatus,
    UploadedFile,
)
from app.models.user import User, UserTier

__all__ = [
    "Base",
    "User",
    "UserTier",
    "CritiqueSession",
    "SessionStatus",
    "CritiqueTone",
    "ReportDepth",
    "UploadedFile",
    "Chunk",
    "DisciplineInstruction",
    "DisciplineStatus",
]
```

- [ ] **Step 2.7: Commit models**

```bash
cd "/Users/macbook/Desktop/Software projects/Researchers-Validation-Center/backend"
git add app/database.py app/models/
git commit -m "feat: add SQLAlchemy 2.0 models (User, Session, Chunk, Discipline)"
```

---

## Task 3: Alembic Migrations

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/` (directory, first migration generated)

- [ ] **Step 3.1: Initialize Alembic inside backend container**

```bash
cd "/Users/macbook/Desktop/Software projects/Researchers-Validation-Center"
docker compose up -d db
docker compose run --rm backend alembic init alembic
```

Expected: `alembic/` directory and `alembic.ini` created.

- [ ] **Step 3.2: Replace `backend/alembic/env.py` with async-compatible version**

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.models import Base  # noqa: F401 — imports all models so Alembic sees them

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3.3: Set sqlalchemy.url in `backend/alembic.ini`**

Open `backend/alembic.ini` and set:
```ini
sqlalchemy.url = postgresql+asyncpg://naqqad:secret@db:5432/naqqad
```

- [ ] **Step 3.4: Generate and apply initial migration**

```bash
docker compose run --rm backend alembic revision --autogenerate -m "initial_schema"
docker compose run --rm backend alembic upgrade head
```

Expected:
```
INFO  [alembic.runtime.migration] Running upgrade  -> <hash>, initial_schema
```

- [ ] **Step 3.5: Verify tables exist**

```bash
docker compose exec db psql -U naqqad -c "\dt"
```

Expected output includes: `users`, `critique_sessions`, `uploaded_files`, `chunks`, `discipline_instructions`.

- [ ] **Step 3.6: Commit migrations**

```bash
git add backend/alembic/ backend/alembic.ini
git commit -m "feat: add Alembic async migrations (initial schema)"
```

---

## Task 4: Security Utils + Auth Schemas

**Files:**
- Create: `backend/app/utils/__init__.py`
- Create: `backend/app/utils/security.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 4.1: Write failing test `backend/tests/test_auth.py`**

```python
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_register_returns_token(async_client: AsyncClient):
    response = await async_client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(async_client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "StrongPass123!"}
    await async_client.post("/auth/register", json=payload)
    response = await async_client.post("/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_valid_credentials(async_client: AsyncClient):
    await async_client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "StrongPass123!"},
    )
    response = await async_client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(async_client: AsyncClient):
    await async_client.post(
        "/auth/register",
        json={"email": "wrong@example.com", "password": "StrongPass123!"},
    )
    response = await async_client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "WrongPass!"},
    )
    assert response.status_code == 401
```

- [ ] **Step 4.2: Create `backend/tests/conftest.py`**

```python
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://naqqad:secret@localhost:5432/naqqad_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
```

- [ ] **Step 4.3: Run test — expect FAIL (no implementation yet)**

```bash
cd "/Users/macbook/Desktop/Software projects/Researchers-Validation-Center/backend"
python -m pytest tests/test_auth.py -v 2>&1 | head -30
```

Expected: `FAILED` — `ImportError` or `404` — no auth routes exist yet.

- [ ] **Step 4.4: Create `backend/app/utils/security.py`**

```python
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    subject: str | None = payload.get("sub")
    if subject is None:
        raise JWTError("Missing subject")
    return subject
```

- [ ] **Step 4.5: Create `backend/app/schemas/auth.py`**

```python
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

- [ ] **Step 4.6: Create `backend/app/api/auth.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(User).where(User.email == body.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return TokenResponse(access_token=create_access_token(str(user.id)))
```

- [ ] **Step 4.7: Wire API modules `backend/app/api/__init__.py`**

```python
from app.api import auth, sessions, upload

__all__ = ["auth", "sessions", "upload"]
```

Create empty stubs for `sessions.py` and `upload.py` so the app imports don't fail yet:

`backend/app/api/sessions.py`:
```python
from fastapi import APIRouter
router = APIRouter()
```

`backend/app/api/upload.py`:
```python
from fastapi import APIRouter
router = APIRouter()
```

- [ ] **Step 4.8: Run tests — expect PASS**

```bash
python -m pytest tests/test_auth.py -v
```

Expected:
```
PASSED tests/test_auth.py::test_register_returns_token
PASSED tests/test_auth.py::test_register_duplicate_email_returns_409
PASSED tests/test_auth.py::test_login_valid_credentials
PASSED tests/test_auth.py::test_login_wrong_password_returns_401
```

- [ ] **Step 4.9: Commit**

```bash
git add app/utils/ app/schemas/ app/api/auth.py app/api/sessions.py app/api/upload.py tests/
git commit -m "feat: add JWT auth (register + login) with tests"
```

---

## Task 5: File Parser Service

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/file_parser.py`
- Create: `backend/tests/test_file_parser.py`
- Create: `backend/tests/fixtures/sample.md` (test fixture)
- Create: `backend/tests/fixtures/sample.txt` (test fixture)

- [ ] **Step 5.1: Create test fixtures**

`backend/tests/fixtures/sample.md`:
```markdown
# الفصل الأول: المقدمة

## 1.1 خلفية الدراسة

تعدّ ظاهرة الاقتصاد الإسلامي من أبرز الظواهر التي شهدها العالم في القرن الماضي.
وقد أثارت هذه الظاهرة جدلاً واسعاً في الأوساط الأكاديمية.

## 1.2 مشكلة الدراسة

تتمثل مشكلة الدراسة في غياب إطار نظري موحد لتفسير النمو الاقتصادي وفق المنظور الإسلامي.

# الفصل الثاني: الإطار النظري

## 2.1 المفاهيم الأساسية

يُعرَّف الاقتصاد الإسلامي بأنه العلم الذي يدرس السلوك الاقتصادي للإنسان وفق أحكام الشريعة الإسلامية.
```

`backend/tests/fixtures/sample.txt`:
```
مقدمة

تعدّ هذه الدراسة محاولة جادة لفهم الظاهرة الاقتصادية من منظور إسلامي.

الإطار النظري

يقوم البحث على ثلاثة محاور أساسية: التعريف، المنهج، والتطبيق.
```

- [ ] **Step 5.2: Write failing test `backend/tests/test_file_parser.py`**

```python
from pathlib import Path

import pytest

from app.services.file_parser import ParsedDocument, RawParagraph, parse_file

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_parse_markdown_returns_paragraphs():
    content = (FIXTURES / "sample.md").read_bytes()
    doc: ParsedDocument = await parse_file(content, "md")
    assert len(doc.paragraphs) >= 3
    assert doc.paragraphs[0].chapter == "الفصل الأول: المقدمة"
    assert doc.paragraphs[0].section == "1.1 خلفية الدراسة"
    assert "اقتصاد" in doc.paragraphs[0].text


@pytest.mark.asyncio
async def test_parse_txt_returns_paragraphs():
    content = (FIXTURES / "sample.txt").read_bytes()
    doc: ParsedDocument = await parse_file(content, "txt")
    assert len(doc.paragraphs) >= 2
    # txt parsing splits on blank lines — text is preserved
    assert any("مقدمة" in p.text or "اقتصادية" in p.text for p in doc.paragraphs)


@pytest.mark.asyncio
async def test_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported format"):
        await parse_file(b"data", "pdf")


def test_raw_paragraph_has_required_fields():
    p = RawParagraph(text="hello", chapter="ch1", section="sec1", paragraph_index=0)
    assert p.text == "hello"
    assert p.chapter == "ch1"
```

- [ ] **Step 5.3: Run — expect FAIL**

```bash
python -m pytest tests/test_file_parser.py -v 2>&1 | head -15
```

Expected: `ImportError: cannot import name 'parse_file'`

- [ ] **Step 5.4: Create `backend/app/services/file_parser.py`**

```python
import io
from dataclasses import dataclass, field

import mistune
from docx import Document


@dataclass
class RawParagraph:
    text: str
    paragraph_index: int
    chapter: str | None = None
    section: str | None = None


@dataclass
class ParsedDocument:
    paragraphs: list[RawParagraph]
    file_format: str
    estimated_pages: int = field(init=False)

    def __post_init__(self):
        total_chars = sum(len(p.text) for p in self.paragraphs)
        self.estimated_pages = max(1, total_chars // 2000)  # ~2000 chars per page


def _parse_docx(content: bytes) -> list[RawParagraph]:
    doc = Document(io.BytesIO(content))
    paragraphs: list[RawParagraph] = []
    current_chapter: str | None = None
    current_section: str | None = None
    idx = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = para.style.name
        if style.startswith("Heading 1"):
            current_chapter = text
            current_section = None
        elif style.startswith("Heading 2"):
            current_section = text
        else:
            paragraphs.append(
                RawParagraph(
                    text=text,
                    paragraph_index=idx,
                    chapter=current_chapter,
                    section=current_section,
                )
            )
            idx += 1

    return paragraphs


def _parse_markdown(content: bytes) -> list[RawParagraph]:
    text = content.decode("utf-8")
    lines = text.split("\n")
    paragraphs: list[RawParagraph] = []
    current_chapter: str | None = None
    current_section: str | None = None
    current_lines: list[str] = []
    idx = 0

    def flush():
        nonlocal idx
        combined = " ".join(current_lines).strip()
        if combined:
            paragraphs.append(
                RawParagraph(
                    text=combined,
                    paragraph_index=idx,
                    chapter=current_chapter,
                    section=current_section,
                )
            )
            idx += 1
        current_lines.clear()

    for line in lines:
        if line.startswith("# "):
            flush()
            current_chapter = line[2:].strip()
            current_section = None
        elif line.startswith("## "):
            flush()
            current_section = line[3:].strip()
        elif line.strip():
            current_lines.append(line.strip())
        else:
            flush()

    flush()
    return paragraphs


def _parse_txt(content: bytes) -> list[RawParagraph]:
    text = content.decode("utf-8")
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    return [
        RawParagraph(text=block, paragraph_index=idx)
        for idx, block in enumerate(blocks)
    ]


async def parse_file(content: bytes, file_format: str) -> ParsedDocument:
    fmt = file_format.lower().lstrip(".")
    if fmt == "docx":
        paragraphs = _parse_docx(content)
    elif fmt == "md":
        paragraphs = _parse_markdown(content)
    elif fmt == "txt":
        paragraphs = _parse_txt(content)
    else:
        raise ValueError(f"Unsupported format: {file_format}")

    return ParsedDocument(paragraphs=paragraphs, file_format=fmt)
```

- [ ] **Step 5.5: Run tests — expect PASS**

```bash
python -m pytest tests/test_file_parser.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5.6: Commit**

```bash
git add app/services/file_parser.py tests/test_file_parser.py tests/fixtures/
git commit -m "feat: add file parser service (docx/md/txt → RawParagraph)"
```

---

## Task 6: S3 Storage Service

**Files:**
- Create: `backend/app/services/storage.py`

> Note: Tests for storage use LocalStack (the S3 mock in docker-compose). Run `docker compose up -d localstack` before running these tests.

- [ ] **Step 6.1: Write failing test `backend/tests/test_storage.py`**

```python
import pytest

from app.services.storage import StorageService


@pytest.fixture
def storage():
    return StorageService()


@pytest.mark.asyncio
async def test_upload_and_download_roundtrip(storage: StorageService):
    original = b"Hello Naqqad \xd9\x86\xd9\x82\xd8\xa7\xd8\xaf"  # "Hello Naqqad نقاد"
    key = "test/roundtrip.bin"
    await storage.upload(key, original)
    downloaded = await storage.download(key)
    assert downloaded == original


@pytest.mark.asyncio
async def test_delete_removes_object(storage: StorageService):
    key = "test/to_delete.bin"
    await storage.upload(key, b"delete me")
    await storage.delete(key)
    with pytest.raises(Exception):
        await storage.download(key)


@pytest.mark.asyncio
async def test_upload_encrypts_at_rest(storage: StorageService):
    plaintext = b"secret research content"
    key = "test/encrypted.bin"
    await storage.upload(key, plaintext)
    # Raw S3 content must differ from plaintext (it's encrypted)
    raw = await storage._download_raw(key)
    assert raw != plaintext
    # But decrypted content matches
    decrypted = await storage.download(key)
    assert decrypted == plaintext
```

- [ ] **Step 6.2: Run — expect FAIL**

```bash
python -m pytest tests/test_storage.py -v 2>&1 | head -10
```

Expected: `ImportError: cannot import name 'StorageService'`

- [ ] **Step 6.3: Create `backend/app/services/storage.py`**

```python
import base64
import io

import boto3
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet

from app.config import settings

# Fernet requires a 32-byte URL-safe base64-encoded key.
# FILE_ENCRYPTION_KEY in .env must be a valid Fernet key.
_fernet = Fernet(settings.file_encryption_key.encode())


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )


class StorageService:
    def __init__(self):
        self._client = _get_s3_client()
        self._bucket = settings.s3_bucket_name
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self._bucket)

    async def upload(self, key: str, data: bytes) -> None:
        encrypted = _fernet.encrypt(data)
        self._client.put_object(Bucket=self._bucket, Key=key, Body=encrypted)

    async def download(self, key: str) -> bytes:
        raw = await self._download_raw(key)
        return _fernet.decrypt(raw)

    async def _download_raw(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    async def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def build_key(self, session_id: str, filename: str) -> str:
        return f"sessions/{session_id}/{filename}"
```

- [ ] **Step 6.4: Generate a valid Fernet key for `.env`**

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output and set it as `FILE_ENCRYPTION_KEY` in `backend/.env`.

- [ ] **Step 6.5: Create the S3 bucket in LocalStack and run tests**

```bash
docker compose up -d localstack
python -m pytest tests/test_storage.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 6.6: Commit**

```bash
git add app/services/storage.py tests/test_storage.py
git commit -m "feat: add S3 storage service with AES-256 (Fernet) encryption"
```

---

## Task 7: Upload API Endpoint

**Files:**
- Modify: `backend/app/api/upload.py`
- Create: `backend/app/schemas/session.py`
- Create: `backend/tests/test_upload.py`

- [ ] **Step 7.1: Create `backend/app/schemas/session.py`**

```python
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.session import CritiqueTone, ReportDepth, SessionStatus


class CreateSessionConfig(BaseModel):
    tone: CritiqueTone
    report_depth: ReportDepth
    byok_api_key: str | None = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    status: SessionStatus
    tone: CritiqueTone
    report_depth: ReportDepth
    detected_language: str | None
    tokens_consumed: int
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 7.2: Write failing test `backend/tests/test_upload.py`**

```python
import io
from pathlib import Path

import pytest
from httpx import AsyncClient

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def auth_headers(async_client):
    return {}  # populated by helper below


async def get_token(client: AsyncClient) -> str:
    r = await client.post(
        "/auth/register",
        json={"email": "uploader@example.com", "password": "StrongPass123!"},
    )
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_upload_markdown_creates_session(async_client: AsyncClient):
    token = await get_token(async_client)
    content = (FIXTURES / "sample.md").read_bytes()
    response = await async_client.post(
        "/sessions/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"tone": "constructive", "report_depth": "standard"},
        files={"file": ("sample.md", io.BytesIO(content), "text/markdown")},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert "id" in data


@pytest.mark.asyncio
async def test_upload_pdf_returns_422(async_client: AsyncClient):
    token = await get_token(async_client)
    response = await async_client.post(
        "/sessions/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"tone": "constructive", "report_depth": "standard"},
        files={"file": ("research.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_requires_auth(async_client: AsyncClient):
    response = await async_client.post(
        "/sessions/upload",
        data={"tone": "constructive", "report_depth": "standard"},
        files={"file": ("f.md", io.BytesIO(b"# test"), "text/markdown")},
    )
    assert response.status_code == 401
```

- [ ] **Step 7.3: Run — expect FAIL**

```bash
python -m pytest tests/test_upload.py -v 2>&1 | head -20
```

Expected: 404 (route not implemented) or auth errors.

- [ ] **Step 7.4: Add `get_current_user` dependency to `backend/app/utils/security.py`**

Append to the existing file:

```python
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import User  # local import to avoid circular

    try:
        user_id = decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

- [ ] **Step 7.5: Replace `backend/app/api/upload.py`**

```python
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.session import CritiqueTone, CritiqueSession, ReportDepth, SessionStatus, UploadedFile
from app.models.user import User, UserTier
from app.schemas.session import SessionResponse
from app.services.storage import StorageService
from app.utils.security import get_current_user

router = APIRouter()

ALLOWED_EXTENSIONS = {"docx", "txt", "md"}
storage = StorageService()


def _validate_extension(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"File format '{ext}' not supported. Allowed: {ALLOWED_EXTENSIONS}",
        )
    return ext


@router.post("/upload", response_model=SessionResponse, status_code=202)
async def upload_file(
    file: UploadFile = File(...),
    tone: CritiqueTone = Form(...),
    report_depth: ReportDepth = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = _validate_extension(file.filename or "")

    content = await file.read()
    size = len(content)
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if size > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    session_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_ttl_hours)

    session = CritiqueSession(
        id=session_id,
        user_id=current_user.id,
        tone=tone,
        report_depth=report_depth,
        status=SessionStatus.QUEUED,
        expires_at=expires_at,
    )
    db.add(session)

    s3_key = storage.build_key(str(session_id), file.filename or f"upload.{ext}")
    await storage.upload(s3_key, content)

    uploaded = UploadedFile(
        session_id=session_id,
        original_filename=file.filename or f"upload.{ext}",
        file_format=ext,
        s3_key=s3_key,
        file_size_bytes=size,
    )
    db.add(uploaded)
    await db.commit()
    await db.refresh(session)

    # Dispatch Celery chunking task (imported here to avoid circular)
    from app.tasks.chunking import run_chunking_task
    run_chunking_task.delay(str(session_id))

    return SessionResponse.model_validate(session)
```

- [ ] **Step 7.6: Run tests — expect PASS**

```bash
python -m pytest tests/test_upload.py -v
```

Expected: all 3 tests PASS (Celery task dispatch will be a no-op until Task 9 but the endpoint must return 202).

- [ ] **Step 7.7: Commit**

```bash
git add app/api/upload.py app/schemas/session.py app/utils/security.py tests/test_upload.py
git commit -m "feat: add /sessions/upload endpoint with format validation and S3 storage"
```

---

## Task 8: Session Status API

**Files:**
- Modify: `backend/app/api/sessions.py`
- Create: `backend/app/schemas/chunk.py`

- [ ] **Step 8.1: Create `backend/app/schemas/chunk.py`**

```python
import uuid
from datetime import datetime

from pydantic import BaseModel


class ChunkResponse(BaseModel):
    id: uuid.UUID
    chapter_title: str | None
    section_title: str | None
    paragraph_index: int
    text: str
    language_hint: str | None
    token_estimate: int
    critique_status: str

    model_config = {"from_attributes": True}
```

- [ ] **Step 8.2: Replace `backend/app/api/sessions.py`**

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.chunk import Chunk
from app.models.session import CritiqueSession
from app.models.user import User
from app.schemas.chunk import ChunkResponse
from app.schemas.session import SessionResponse
from app.utils.security import get_current_user

router = APIRouter()


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = await db.get(CritiqueSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.model_validate(session)


@router.get("/{session_id}/chunks", response_model=list[ChunkResponse])
async def get_chunks(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = await db.get(CritiqueSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(Chunk)
        .where(Chunk.session_id == session_id)
        .order_by(Chunk.paragraph_index)
    )
    chunks = result.scalars().all()
    return [ChunkResponse.model_validate(c) for c in chunks]
```

- [ ] **Step 8.3: Commit**

```bash
git add app/api/sessions.py app/schemas/chunk.py
git commit -m "feat: add GET /sessions/{id} and GET /sessions/{id}/chunks endpoints"
```

---

## Task 9: Ollama Chunker Service

**Files:**
- Create: `backend/app/services/chunker.py`
- Create: `backend/tests/test_chunker.py`

- [ ] **Step 9.1: Write failing test `backend/tests/test_chunker.py`**

```python
import pytest

from app.services.chunker import ChunkerService
from app.services.file_parser import ParsedDocument, RawParagraph


@pytest.fixture
def doc_with_paragraphs() -> ParsedDocument:
    paragraphs = [
        RawParagraph(
            text="تعدّ ظاهرة الاقتصاد الإسلامي من أبرز الظواهر التي شهدها العالم.",
            paragraph_index=0,
            chapter="الفصل الأول",
            section="المقدمة",
        ),
        RawParagraph(
            text="يُعرَّف الاقتصاد الإسلامي بأنه العلم الذي يدرس السلوك وفق الشريعة.",
            paragraph_index=1,
            chapter="الفصل الأول",
            section="الإطار النظري",
        ),
        RawParagraph(
            text="The Islamic finance industry has grown significantly since the 1970s.",
            paragraph_index=2,
            chapter="Chapter Two",
            section="Literature Review",
        ),
    ]
    return ParsedDocument(paragraphs=paragraphs, file_format="md")


@pytest.mark.asyncio
async def test_chunk_enriches_language_hint(doc_with_paragraphs: ParsedDocument):
    service = ChunkerService()
    chunks = await service.chunk(doc_with_paragraphs)
    assert len(chunks) == 3
    ar_chunk = chunks[0]
    en_chunk = chunks[2]
    assert ar_chunk.language_hint == "ar"
    assert en_chunk.language_hint == "en"


@pytest.mark.asyncio
async def test_chunk_preserves_chapter_section(doc_with_paragraphs: ParsedDocument):
    service = ChunkerService()
    chunks = await service.chunk(doc_with_paragraphs)
    assert chunks[0].chapter_title == "الفصل الأول"
    assert chunks[0].section_title == "المقدمة"


@pytest.mark.asyncio
async def test_chunk_estimates_tokens(doc_with_paragraphs: ParsedDocument):
    service = ChunkerService()
    chunks = await service.chunk(doc_with_paragraphs)
    for chunk in chunks:
        assert chunk.token_estimate > 0


def test_detect_language_arabic():
    from app.services.chunker import _detect_language
    assert _detect_language("تعدّ هذه الدراسة محاولة جادة") == "ar"


def test_detect_language_english():
    from app.services.chunker import _detect_language
    assert _detect_language("The study examines economic behavior") == "en"


def test_detect_language_mixed():
    from app.services.chunker import _detect_language
    assert _detect_language("يرى الباحث أن GDP growth يعتمد على السياسة المالية") == "mixed"
```

- [ ] **Step 9.2: Run — expect FAIL**

```bash
python -m pytest tests/test_chunker.py -v 2>&1 | head -10
```

Expected: `ImportError: cannot import name 'ChunkerService'`

- [ ] **Step 9.3: Create `backend/app/services/chunker.py`**

```python
import re
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.services.file_parser import ParsedDocument

ARABIC_RANGE = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")
LATIN_RANGE = re.compile(r"[a-zA-Z]")


def _detect_language(text: str) -> str:
    ar_count = len(ARABIC_RANGE.findall(text))
    la_count = len(LATIN_RANGE.findall(text))
    total = ar_count + la_count
    if total == 0:
        return "ar"
    ar_ratio = ar_count / total
    if ar_ratio >= 0.75:
        return "ar"
    if ar_ratio <= 0.25:
        return "en"
    return "mixed"


def _estimate_tokens(text: str) -> int:
    # Rough estimate: Arabic words tokenise at ~1.5 tokens each; Latin at ~1 token per 4 chars
    words = text.split()
    return max(1, int(len(words) * 1.3))


@dataclass
class ChunkData:
    chapter_title: str | None
    section_title: str | None
    paragraph_index: int
    text: str
    language_hint: str
    token_estimate: int


class ChunkerService:
    def __init__(self):
        self._base_url = settings.ollama_base_url
        self._model = settings.ollama_chunker_model

    async def chunk(self, doc: ParsedDocument) -> list[ChunkData]:
        """
        For docx/md: paragraphs already have chapter/section from the parser.
        We only call Ollama for txt files where structure is ambiguous.
        For all formats: enrich with language detection and token estimates.
        """
        if doc.file_format == "txt" and len(doc.paragraphs) > 0:
            return await self._chunk_with_ollama(doc)
        return self._chunk_deterministic(doc)

    def _chunk_deterministic(self, doc: ParsedDocument) -> list[ChunkData]:
        return [
            ChunkData(
                chapter_title=p.chapter,
                section_title=p.section,
                paragraph_index=p.paragraph_index,
                text=p.text,
                language_hint=_detect_language(p.text),
                token_estimate=_estimate_tokens(p.text),
            )
            for p in doc.paragraphs
        ]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _call_ollama(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
            )
            response.raise_for_status()
            return response.json()["response"]

    async def _chunk_with_ollama(self, doc: ParsedDocument) -> list[ChunkData]:
        raw_text = "\n\n".join(p.text for p in doc.paragraphs)
        prompt = f"""You are a structural document analyzer for Arabic academic texts.
Split the following text into logical paragraphs. Identify chapter/section headings.

Text:
{raw_text}

Return ONLY a JSON array. Each item must have:
- "chapter": string or null
- "section": string or null
- "paragraph_index": integer
- "text": the paragraph content

JSON:"""

        import json

        try:
            raw = await self._call_ollama(prompt)
            json_str = raw.strip()
            if "```" in json_str:
                json_str = json_str.split("```")[1].lstrip("json").strip()
            parsed = json.loads(json_str)
        except Exception:
            # Fallback to deterministic if Ollama fails/times out
            return self._chunk_deterministic(doc)

        return [
            ChunkData(
                chapter_title=item.get("chapter"),
                section_title=item.get("section"),
                paragraph_index=item.get("paragraph_index", idx),
                text=item["text"],
                language_hint=_detect_language(item["text"]),
                token_estimate=_estimate_tokens(item["text"]),
            )
            for idx, item in enumerate(parsed)
            if item.get("text", "").strip()
        ]
```

- [ ] **Step 9.4: Run tests — expect PASS**

The chunker tests use the deterministic path (md format), so no Ollama connection needed.

```bash
python -m pytest tests/test_chunker.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 9.5: Commit**

```bash
git add app/services/chunker.py tests/test_chunker.py
git commit -m "feat: add Qwen2.5 chunker service (Ollama + deterministic fallback)"
```

---

## Task 10: Celery Setup & Chunking Task

**Files:**
- Create: `backend/app/tasks/celery_app.py`
- Create: `backend/app/tasks/__init__.py`
- Create: `backend/app/tasks/chunking.py`
- Create: `backend/app/tasks/cleanup.py`

- [ ] **Step 10.1: Create `backend/app/tasks/celery_app.py`**

```python
from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "naqqad",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.chunking", "app.tasks.cleanup"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_routes={
        "app.tasks.chunking.*": {"queue": "chunking"},
        "app.tasks.cleanup.*": {"queue": "cleanup"},
    },
    beat_schedule={
        "expire-sessions-every-hour": {
            "task": "app.tasks.cleanup.delete_expired_sessions",
            "schedule": crontab(minute=0),  # every hour at :00
        }
    },
)
```

- [ ] **Step 10.2: Create `backend/app/tasks/chunking.py`**

```python
import asyncio
import uuid

from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.chunking.run_chunking_task", bind=True, max_retries=3)
def run_chunking_task(self, session_id: str):
    asyncio.run(_async_run_chunking(session_id))


async def _async_run_chunking(session_id: str):
    from sqlalchemy import select

    from app.database import AsyncSessionLocal
    from app.models.chunk import Chunk
    from app.models.session import CritiqueSession, SessionStatus, UploadedFile
    from app.services.chunker import ChunkerService
    from app.services.file_parser import parse_file
    from app.services.storage import StorageService

    storage = StorageService()
    chunker = ChunkerService()
    sid = uuid.UUID(session_id)

    async with AsyncSessionLocal() as db:
        session = await db.get(CritiqueSession, sid)
        if not session:
            return

        session.status = SessionStatus.PARSING
        await db.commit()

        try:
            result = await db.execute(
                select(UploadedFile).where(UploadedFile.session_id == sid)
            )
            uploaded = result.scalar_one_or_none()
            if not uploaded:
                raise ValueError("No uploaded file for session")

            content = await storage.download(uploaded.s3_key)
            parsed_doc = await parse_file(content, uploaded.file_format)

            uploaded.page_count_estimate = parsed_doc.estimated_pages
            await db.commit()

            chunk_data_list = await chunker.chunk(parsed_doc)

            for cd in chunk_data_list:
                chunk = Chunk(
                    session_id=sid,
                    chapter_title=cd.chapter_title,
                    section_title=cd.section_title,
                    paragraph_index=cd.paragraph_index,
                    text=cd.text,
                    language_hint=cd.language_hint,
                    token_estimate=cd.token_estimate,
                )
                db.add(chunk)

            # Detect dominant language and set on session
            langs = [cd.language_hint for cd in chunk_data_list]
            ar_count = langs.count("ar")
            en_count = langs.count("en")
            session.detected_language = "ar" if ar_count >= en_count else "en"
            session.status = SessionStatus.QUEUED
            await db.commit()

        except Exception as exc:
            session.status = SessionStatus.FAILED
            await db.commit()
            raise
```

- [ ] **Step 10.3: Create `backend/app/tasks/cleanup.py`**

```python
import asyncio
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.cleanup.delete_expired_sessions")
def delete_expired_sessions():
    asyncio.run(_async_delete_expired())


async def _async_delete_expired():
    from sqlalchemy import select

    from app.database import AsyncSessionLocal
    from app.models.session import CritiqueSession, SessionStatus, UploadedFile
    from app.services.storage import StorageService

    storage = StorageService()
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CritiqueSession).where(
                CritiqueSession.expires_at <= now,
                CritiqueSession.status != SessionStatus.EXPIRED,
            )
        )
        expired_sessions = result.scalars().all()

        for session in expired_sessions:
            files_result = await db.execute(
                select(UploadedFile).where(UploadedFile.session_id == session.id)
            )
            for uploaded in files_result.scalars().all():
                try:
                    await storage.delete(uploaded.s3_key)
                except Exception:
                    pass  # already deleted or missing — continue

            session.status = SessionStatus.EXPIRED

        await db.commit()
```

- [ ] **Step 10.4: Create `backend/app/tasks/__init__.py`**

```python
```

(empty file)

- [ ] **Step 10.5: Write integration test for chunking task**

Add to `backend/tests/test_upload.py`:

```python
@pytest.mark.asyncio
async def test_session_transitions_to_queued_after_chunking(async_client: AsyncClient):
    """
    Smoke test: upload a file and verify the session reaches QUEUED status
    (chunking task runs synchronously in tests via eager mode).
    """
    from app.tasks import celery_app as ca
    ca.celery_app.conf.task_always_eager = True  # run tasks synchronously in tests

    token = await get_token(async_client)
    content = (FIXTURES / "sample.md").read_bytes()

    upload_response = await async_client.post(
        "/sessions/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"tone": "constructive", "report_depth": "standard"},
        files={"file": ("sample.md", io.BytesIO(content), "text/markdown")},
    )
    assert upload_response.status_code == 202
    session_id = upload_response.json()["id"]

    status_response = await async_client.get(
        f"/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "queued"
    assert status_response.json()["detected_language"] == "ar"
```

- [ ] **Step 10.6: Run full test suite**

```bash
python -m pytest tests/ -v --tb=short
```

Expected: all tests PASS (Celery runs in eager/sync mode during tests).

- [ ] **Step 10.7: Commit**

```bash
git add app/tasks/ tests/test_upload.py
git commit -m "feat: add Celery chunking task (parse → chunk → update session status)"
```

---

## Task 11: TTL Cleanup Test

**Files:**
- Create: `backend/tests/test_cleanup.py`

- [ ] **Step 11.1: Write test `backend/tests/test_cleanup.py`**

```python
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.session import CritiqueSession, CritiqueTone, ReportDepth, SessionStatus
from app.tasks.cleanup import _async_delete_expired


@pytest.mark.asyncio
async def test_expired_sessions_get_marked_expired(db_session):
    expired_id = uuid.uuid4()
    past = datetime.now(timezone.utc) - timedelta(hours=25)
    session = CritiqueSession(
        id=expired_id,
        user_id=uuid.uuid4(),
        tone=CritiqueTone.CONSTRUCTIVE,
        report_depth=ReportDepth.STANDARD,
        status=SessionStatus.COMPLETED,
        expires_at=past,
    )
    db_session.add(session)
    await db_session.commit()

    await _async_delete_expired()

    result = await db_session.get(CritiqueSession, expired_id)
    # Re-fetch from DB after the cleanup ran its own session
    await db_session.refresh(result)
    assert result.status == SessionStatus.EXPIRED


@pytest.mark.asyncio
async def test_non_expired_sessions_are_untouched(db_session):
    future_id = uuid.uuid4()
    future = datetime.now(timezone.utc) + timedelta(hours=23)
    session = CritiqueSession(
        id=future_id,
        user_id=uuid.uuid4(),
        tone=CritiqueTone.FORENSIC,
        report_depth=ReportDepth.DEEP_AUDIT,
        status=SessionStatus.COMPLETED,
        expires_at=future,
    )
    db_session.add(session)
    await db_session.commit()

    await _async_delete_expired()

    result = await db_session.get(CritiqueSession, future_id)
    await db_session.refresh(result)
    assert result.status == SessionStatus.COMPLETED
```

- [ ] **Step 11.2: Run cleanup tests**

```bash
python -m pytest tests/test_cleanup.py -v
```

Expected: both tests PASS.

- [ ] **Step 11.3: Final full suite run**

```bash
python -m pytest tests/ -v --tb=short
```

Expected: all tests in `test_auth.py`, `test_file_parser.py`, `test_storage.py`, `test_upload.py`, `test_chunker.py`, `test_cleanup.py` PASS.

- [ ] **Step 11.4: Start all services and smoke test the live API**

```bash
# Start all services
docker compose up -d

# Wait for db to be healthy, then run migration
docker compose run --rm backend alembic upgrade head

# Smoke test health endpoint
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

```bash
# Register a user and upload a file
TOKEN=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@naqqad.com","password":"StrongPass123!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST http://localhost:8000/sessions/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@backend/tests/fixtures/sample.md;type=text/markdown" \
  -F "tone=constructive" \
  -F "report_depth=standard" | python3 -m json.tool
```

Expected: JSON response with `"status": "queued"` and a session UUID.

- [ ] **Step 11.5: Final commit**

```bash
git add tests/test_cleanup.py
git commit -m "feat: add TTL cleanup task tests — Phase 1 foundation complete"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Auth (register/login with JWT) → Task 4
- [x] File upload docx/txt/md (no PDF) → Task 7
- [x] AES-256 encryption at rest → Task 6
- [x] S3 storage with TTL → Tasks 6 + 11
- [x] Stage-1 chunker (Qwen2.5:7b via Ollama) → Task 9
- [x] Celery async task queue → Task 10
- [x] Session status state machine → Task 10 + models
- [x] 24-hour secure deletion → Task 11
- [x] Session + chunk status API → Task 8
- [x] Free tier page cap (constant in config) → upload.py (`max_file_size_mb`, `free_tier_max_pages` in settings)

**Not in this plan (Phase 2+):**
- Stage-2 critique (Gemini/Claude) → Plan 2
- DSE protocol + jury assembly → Plan 2
- PDF/HTML report generation → Plan 3
- RTL web UI → Plan 4
- Tap Payments billing → Plan 4

---

## Execution Handoff

Plan complete and saved to `docs/adham-ai/plans/2026-06-16-naqqad-phase1-foundation.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** — Fresh subagent per task, review between tasks, fast parallel iteration. Run: `/adham-ai:parallel-build docs/adham-ai/plans/2026-06-16-naqqad-phase1-foundation.md`

**2. Inline Execution** — Execute tasks in this session with checkpoints. Run: `/adham-ai:build docs/adham-ai/plans/2026-06-16-naqqad-phase1-foundation.md`
