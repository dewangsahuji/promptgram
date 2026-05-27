# Promptgram — Microservices Backend

A prompt-sharing platform built with FastAPI, decomposed into independently deployable microservices with AI-powered image search, auto-tagging, and NSFW moderation.

## Architecture

```
                    ┌──────────────────────────┐
                    │      React Frontend        │
                    └──────────────┬────────────┘
                                   │ HTTP :80
                    ┌──────────────▼────────────┐
                    │      Nginx API Gateway      │
                    └───┬────────┬────────┬───┬──┘
                        │        │        │   │
             ┌──────────▼──┐ ┌───▼────┐ ┌▼──────┐ ┌───▼────┐
             │    Auth      │ │ Prompt │ │Social │ │   AI   │
             │   :8001      │ │ :8002  │ │ :8003 │ │ :8004  │
             └──────┬───────┘ └───┬────┘ └───────┘ └───┬────┘
                    │             │                      │
             ┌──────▼─────────────▼──────────────────────▼────┐
             │   PostgreSQL  │  Redis  │  MinIO  │  Qdrant     │
             └─────────────────────────────────────────────────┘
```

## Services

| Service | Port | Responsibilities |
|---|---|---|
| **Auth** | 8001 | Registration, login, logout, JWT issuance |
| **Prompt** | 8002 | Prompt CRUD, image uploads to S3/MinIO, Redis trending feed |
| **Social** | 8003 | Likes, comments, follows, collections, user profiles |
| **AI** | 8004 | CLIP embeddings, semantic search, auto-tagging, NSFW moderation |
| **Nginx** | 80 | API gateway — path-based routing to all services |

## Infrastructure

| Container | Image | Purpose |
|---|---|---|
| `promptgram_postgres` | postgres:16 | Primary DB — one schema per service |
| `promptgram_redis` | redis:7-alpine | JWT blacklist + trending cache |
| `promptgram_minio` | minio/minio | S3-compatible local image storage |
| `promptgram_qdrant` | qdrant/qdrant:v1.9.0 | Vector DB for CLIP embeddings |

## Quick Start

### 1. Configure environment files

```bash
cp services/auth/.env.example   services/auth/.env
cp services/prompt/.env.example services/prompt/.env
cp services/social/.env.example services/social/.env
cp services/ai/.env.example     services/ai/.env
```

**Set the same `JWT_SECRET` in all 4 `.env` files.**

### 2. Start all services

```bash
docker compose up --build
```

> ⚠️ **First build takes 5–10 minutes.** The AI service installs PyTorch CPU + downloads CLIP weights (~1.5 GB image). Subsequent builds are cached.

### 3. Verify all services are healthy

```bash
curl http://localhost/health              # Nginx gateway
curl http://localhost:8001/health        # Auth
curl http://localhost:8002/health        # Prompt
curl http://localhost:8003/health        # Social
curl http://localhost:8004/health        # AI  (models_loaded: true after ~60s)
```

### 4. Access API docs

| Service | Swagger UI |
|---|---|
| Auth | http://localhost:8001/docs |
| Prompt | http://localhost:8002/docs |
| Social | http://localhost:8003/docs |
| AI | http://localhost:8004/docs |
| MinIO Console | http://localhost:9001 (`minioadmin` / `minioadmin`) |
| Qdrant Dashboard | http://localhost:6334/dashboard |

---

## API Routes (via Nginx gateway on :80)

### Auth — `/api/auth/`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/signup` | ❌ | Register + get JWT |
| POST | `/api/auth/login` | ❌ | Login (OAuth2 form) |
| GET | `/api/auth/me` | ✅ | Current user profile |
| POST | `/api/auth/logout` | ✅ | Blacklist token (24h TTL) |
| GET | `/api/auth/users/{id}` | ❌ | Public user lookup |

### Prompts — `/api/prompts/`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/prompts/` | ✅ | Create prompt |
| GET | `/api/prompts/` | ❌ | List prompts (paginated) |
| GET | `/api/prompts/trending` | ❌ | Trending (Redis cached 10 min) |
| GET | `/api/prompts/{id}` | ❌ | Get prompt + increment views |
| PATCH | `/api/prompts/{id}` | ✅ | Update prompt (owner only) |
| DELETE | `/api/prompts/{id}` | ✅ | Delete prompt (owner only) |

### Images — `/api/images/`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/images/upload?prompt_id=` | ✅ | Upload image (auto-triggers AI pipeline) |
| GET | `/api/images/prompt/{id}` | ❌ | List images for a prompt |
| DELETE | `/api/images/{id}` | ✅ | Delete image + S3 cleanup |

### Social — `/api/`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/like/{prompt_id}` | ✅ | Toggle like |
| GET | `/api/like/{prompt_id}/count` | ❌ | Like count |
| POST | `/api/comment/{prompt_id}` | ✅ | Add comment |
| GET | `/api/comment/{prompt_id}` | ❌ | Get comments |
| DELETE | `/api/comment/{id}` | ✅ | Delete comment (owner) |
| POST | `/api/follow/{user_id}` | ✅ | Toggle follow |
| GET | `/api/follow/{user_id}/followers` | ❌ | Follower list |
| GET | `/api/follow/{user_id}/following` | ❌ | Following list |
| POST | `/api/collections/` | ✅ | Create collection |
| GET | `/api/collections/my` | ✅ | My collections |
| POST | `/api/collections/{id}/prompts` | ✅ | Add prompt to collection |
| GET | `/api/users/{id}` | ❌ | User profile (proxied to Auth) |
| GET | `/api/users/{id}/prompts` | ❌ | User's prompts (proxied to Prompt) |

### AI — `/api/ai/`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/ai/embed` | ❌ | CLIP embed image → store in Qdrant |
| POST | `/api/ai/search` | ❌ | Text query → vector → similar images |
| POST | `/api/ai/similar-images` | ❌ | Find visually similar images by ID |
| POST | `/api/ai/classify` | ❌ | MobileNetV3 auto-tag + quality score |
| POST | `/api/ai/moderate` | ❌ | NudeNet NSFW detection |
| POST | `/api/ai/pipeline/{image_id}` | ❌ | Full pipeline (moderate→classify→embed) |

---

## AI Pipeline

After every image upload, the prompt-service fires a **BackgroundTask** that calls:

```
POST /ai/pipeline/{image_id}
```

Which runs in sequence:

```
1. Moderate  → NudeNet NSFW check → PATCH /images/{id}/nsfw
2. Classify  → MobileNetV3 tags  → PATCH /prompts/{id}/tags + score
3. Embed     → CLIP ViT-B/32     → Qdrant upsert → PATCH /images/{id}/qdrant
```

### AI Models

| Model | Size | Task |
|---|---|---|
| CLIP ViT-B/32 (`open_clip_torch`) | ~350 MB | Image + text embeddings (512D) |
| MobileNetV3-Large (`torchvision`) | ~22 MB | ImageNet classification → auto-tags |
| NudeNet (`nudenet`) | ~80 MB | NSFW detection (ONNX-backed) |

> All models run on **CPU** — no GPU required.

### Semantic Search Example

```bash
# Find images matching a text description
curl -X POST http://localhost/api/ai/search \
  -H "Content-Type: application/json" \
  -d '{"query": "a cyberpunk cityscape at night", "limit": 10}'

# Find visually similar images
curl -X POST http://localhost/api/ai/similar-images \
  -H "Content-Type: application/json" \
  -d '{"image_id": "<uuid>", "limit": 5}'
```

---

## Database Migrations (Alembic)

Each service manages its own schema independently:

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

# AI service has no DB (stateless — Qdrant is the store)
```

---

## Project Structure

```
promptgram/
├── docker-compose.yaml          ← Orchestrates all 8 containers
├── nginx/nginx.conf             ← API gateway routing
├── scripts/init-dbs.sql         ← Creates auth_db, prompt_db, social_db
├── README.md
└── services/
    ├── auth/                    ← Auth microservice  (port 8001)
    │   ├── Dockerfile
    │   ├── main.py
    │   ├── alembic/
    │   ├── models/user.py
    │   ├── schemas/
    │   ├── routers/auth.py
    │   ├── services/auth_service.py
    │   └── dependencies/auth.py
    ├── prompt/                  ← Prompt microservice (port 8002)
    │   ├── Dockerfile
    │   ├── main.py
    │   ├── alembic/
    │   ├── models/  (prompt.py, image.py)
    │   ├── schemas/
    │   ├── routers/ (prompts.py, images.py)
    │   ├── services/prompt_service.py
    │   └── s3_client.py
    ├── social/                  ← Social microservice  (port 8003)
    │   ├── Dockerfile
    │   ├── main.py
    │   ├── alembic/
    │   ├── models/social.py
    │   ├── schemas/
    │   └── routers/ (social.py, collections.py, users.py)
    └── ai/                      ← AI microservice      (port 8004)
        ├── Dockerfile
        ├── main.py              ← Loads all models at startup
        ├── model_manager.py     ← CLIP + MobileNetV3 + NudeNet
        ├── qdrant_client_helper.py
        ├── config.py
        └── routers/
            ├── embed.py         ← CLIP image embedding
            ├── search.py        ← Semantic + similar-image search
            ├── classify.py      ← Auto-tagging + quality score
            ├── moderate.py      ← NSFW detection
            └── pipeline.py      ← Full pipeline entrypoint
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| JWT validated locally in each service | No network hop per request — shared `JWT_SECRET` |
| No cross-service DB foreign keys | Services own their data; references are plain UUIDs |
| Separate Postgres DB per service | Isolation without running multiple Postgres instances |
| AI pipeline as BackgroundTask | Upload returns immediately; AI runs async in background |
| CPU-only PyTorch | No GPU required — runs on any VPS or laptop |
| Qdrant for vector storage | Persistent, fast cosine similarity, self-hosted |
| Social service proxies user/prompt data | Thin `httpx` proxy — keeps data ownership clean |

---

## Local Dev (without Docker)

```bash
# Start infrastructure only
docker compose up postgres redis minio qdrant -d

# Run a service locally
cd services/auth
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Run AI service locally (slow first start — downloads models)
cd services/ai
pip install -r requirements.txt
uvicorn main:app --reload --port 8004
```

---

## Environment Variables Reference

### All services share:
```env
JWT_SECRET=your-secret-key   # Must be identical across all services
```

### Auth service
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/auth_db
REDIS_URL=redis://redis:6379/0
```

### Prompt service
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/prompt_db
REDIS_URL=redis://redis:6379/1
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_REGION=us-east-1
S3_BUCKET_NAME=promptgram-images
S3_ENDPOINT_URL=http://minio:9000   # Remove for real AWS S3
AI_SERVICE_URL=http://ai-service:8004
```

### Social service
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/social_db
REDIS_URL=redis://redis:6379/2
PROMPT_SERVICE_URL=http://prompt-service:8002
AUTH_SERVICE_URL=http://auth-service:8001
```

### AI service
```env
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=prompt_images
PROMPT_SERVICE_URL=http://prompt-service:8002
```
