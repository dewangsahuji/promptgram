# Promptgram — Microservices Backend

A prompt-sharing platform built with FastAPI, decomposed into independently deployable microservices.

## Architecture

```
                    ┌──────────────────────┐
                    │   React Frontend      │
                    └──────────┬───────────┘
                               │ HTTP :80
                    ┌──────────▼───────────┐
                    │   Nginx API Gateway   │
                    └──┬───────┬───────┬───┘
                       │       │       │
             ┌─────────▼─┐ ┌───▼────┐ ┌▼──────────┐
             │   Auth     │ │ Prompt │ │  Social   │
             │  :8001     │ │ :8002  │ │  :8003    │
             └─────┬──────┘ └───┬────┘ └─────┬─────┘
                   │            │             │
             ┌─────▼────────────▼─────────────▼─────┐
             │  PostgreSQL  |  Redis  |  MinIO (S3)  │
             └──────────────────────────────────────┘
```

## Services

| Service | Port | Responsibilities |
|---|---|---|
| **Auth** | 8001 | Registration, login, logout, JWT issuance |
| **Prompt** | 8002 | Prompt CRUD, image uploads, S3, trending feed |
| **Social** | 8003 | Likes, comments, follows, collections, user profiles |
| **Nginx** | 80 | API gateway, path-based routing to all services |

## Quick Start

### 1. Configure environment files

Copy and fill in each service's `.env.example`:
```bash
cp services/auth/.env.example     services/auth/.env
cp services/prompt/.env.example   services/prompt/.env
cp services/social/.env.example   services/social/.env
```

**Minimum required for local dev (shared secret must match across all services):**
```env
JWT_SECRET=your-super-secret-key-change-in-production
```

### 2. Start all services
```bash
docker compose up --build
```

### 3. Verify health
```bash
curl http://localhost/health                    # Nginx gateway
curl http://localhost:8001/health              # Auth service
curl http://localhost:8002/health              # Prompt service
curl http://localhost:8003/health              # Social service
```

### 4. Access API docs
| Service | Swagger UI |
|---|---|
| Auth | http://localhost:8001/docs |
| Prompt | http://localhost:8002/docs |
| Social | http://localhost:8003/docs |

## API Routes (via Nginx)

| Method | Path | Service | Auth |
|---|---|---|---|
| POST | /api/auth/signup | auth | ❌ |
| POST | /api/auth/login | auth | ❌ |
| POST | /api/auth/logout | auth | ✅ |
| GET | /api/auth/me | auth | ✅ |
| POST | /api/prompts/ | prompt | ✅ |
| GET | /api/prompts/ | prompt | ❌ |
| GET | /api/prompts/trending | prompt | ❌ |
| GET | /api/prompts/{id} | prompt | ❌ |
| PATCH | /api/prompts/{id} | prompt | ✅ |
| DELETE | /api/prompts/{id} | prompt | ✅ |
| POST | /api/images/upload | prompt | ✅ |
| POST | /api/like/{prompt_id} | social | ✅ |
| POST | /api/comment/{prompt_id} | social | ✅ |
| POST | /api/follow/{user_id} | social | ✅ |
| POST | /api/collections/ | social | ✅ |
| GET | /api/users/{user_id} | social | ❌ |

## Database Migrations (Alembic)

Each service manages its own database schema. Run migrations per-service:

```bash
# Auth service
docker compose exec auth-service alembic revision --autogenerate -m "initial"
docker compose exec auth-service alembic upgrade head

# Prompt service
docker compose exec prompt-service alembic revision --autogenerate -m "initial"
docker compose exec prompt-service alembic upgrade head

# Social service
docker compose exec social-service alembic revision --autogenerate -m "initial"
docker compose exec social-service alembic upgrade head
```

## Project Structure

```
promptgram/
├── docker-compose.yaml          ← Orchestrates all services
├── nginx/
│   └── nginx.conf               ← API gateway routing
├── scripts/
│   └── init-dbs.sql             ← Creates auth_db, prompt_db, social_db
└── services/
    ├── auth/                    ← Auth microservice (port 8001)
    │   ├── Dockerfile
    │   ├── main.py
    │   ├── alembic/
    │   ├── models/
    │   ├── schemas/
    │   ├── routers/
    │   ├── services/
    │   └── dependencies/
    ├── prompt/                  ← Prompt microservice (port 8002)
    │   ├── Dockerfile
    │   ├── main.py
    │   ├── alembic/
    │   ├── models/
    │   ├── schemas/
    │   ├── routers/
    │   ├── services/
    │   └── dependencies/
    └── social/                  ← Social microservice (port 8003)
        ├── Dockerfile
        ├── main.py
        ├── alembic/
        ├── models/
        ├── schemas/
        ├── routers/
        ├── services/
        └── dependencies/
```

## Key Design Decisions

- **JWT shared secret** — All services validate JWTs locally using the same `JWT_SECRET`. No Auth service call needed per request.
- **Database isolation** — Each service has its own Postgres database (`auth_db`, `prompt_db`, `social_db`) on the same Postgres instance.
- **No cross-service FK constraints** — Services reference each other by UUID only; referential integrity is maintained at application level.
- **Inter-service communication** — `httpx` async HTTP calls (Social → Auth for user profiles, Social → Prompt for user prompts).
- **Token blacklisting** — Redis shared across services for logout (JWT blacklist pattern).

## Local Dev (without Docker)

```bash
# Start infrastructure only
docker compose up postgres redis minio -d

# Run a service locally
cd services/auth
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```
