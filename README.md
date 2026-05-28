# ✦ Promptgram

A full-stack **AI-powered prompt sharing platform** — think Instagram, but for AI prompts and generated images. Built with a React frontend, FastAPI microservices backend, and a self-hosted AI pipeline that automatically moderates, classifies, and semantically indexes every uploaded image.

---

## ✨ Features

- 🖼️ **Upload prompts + images** — drag & drop with live preview, 10 MB limit
- 🔍 **Semantic search** — find images by describing them in plain English (CLIP embeddings)
- 🤖 **Auto AI pipeline** — every upload is automatically moderated (NSFW), classified (auto-tags), and embedded (Qdrant)
- 🔥 **Trending feed** — Redis-cached feed ranked by views + downloads + quality score
- 💬 **Social layer** — likes, comments, follows, collections
- 🌙 **Dark / Light mode** — persisted to localStorage
- 🔐 **JWT auth** — stateless tokens blacklisted in Redis on logout

---

## 🏗️ Architecture

```
                    ┌────────────────────────────┐
                    │      React SPA (Vite)       │
                    │   Sidebar · Feed · Detail   │
                    └──────────────┬──────────────┘
                                   │ HTTP :80
                    ┌──────────────▼──────────────┐
                    │      Nginx API Gateway       │
                    │    (path-based routing)      │
                    └───┬────────┬────────┬────┬───┘
                        │        │        │    │
             ┌──────────▼──┐ ┌───▼────┐ ┌▼───────┐ ┌───▼────┐
             │  Auth       │ │ Prompt │ │ Social │ │   AI   │
             │  :8001      │ │ :8002  │ │ :8003  │ │ :8004  │
             └──────┬──────┘ └───┬────┘ └────────┘ └───┬────┘
                    │            │                       │
             ┌──────▼────────────▼───────────────────────▼─────┐
             │  PostgreSQL    │  Redis   │  MinIO  │  Qdrant    │
             │  (3 databases) │ (cache)  │  (S3)   │ (vectors)  │
             └────────────────────────────────────────────────--┘
```

### Services

| Service | Port | Responsibilities |
|---|---|---|
| **Auth** | 8001 | Registration, login, logout, JWT issuance & blacklisting |
| **Prompt** | 8002 | Prompt CRUD, image upload to S3, trending feed, enriched responses |
| **Social** | 8003 | Likes, comments, follows, collections, user profiles |
| **AI** | 8004 | CLIP embeddings, semantic search, auto-tagging, NSFW moderation |
| **Nginx** | 80 | API gateway — path-based routing, SPA catch-all, static assets |

### Infrastructure

| Container | Image | Purpose |
|---|---|---|
| `promptgram_postgres` | `postgres:16` | Primary DB — `auth_db`, `prompt_db`, `social_db` |
| `promptgram_redis` | `redis:7-alpine` | JWT blacklist + trending cache (10 min TTL) |
| `promptgram_minio` | `minio/minio` | S3-compatible local image storage |
| `promptgram_qdrant` | `qdrant/qdrant:v1.9.0` | Vector DB for CLIP 512D embeddings |

---

## 🚀 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- 4 GB free RAM (AI service loads ~500 MB of ML models)
- 4 GB free disk (Docker images + model weights)

### 1. Clone & configure

```bash
git clone <repo-url>
cd promptgram
```

Edit environment files — **the same `JWT_SECRET` must appear in all 4 files**:

```bash
# services/auth/.env
DATABASE_URL="postgresql+asyncpg://postgres:password@postgres:5432/auth_db"
REDIS_URL="redis://redis:6379/0"
JWT_SECRET="your-secret-key-min-32-chars"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# For image storage — choose one:
# Option A: Real AWS S3
AWS_ACCESS_KEY_ID="AKIA..."
AWS_SECRET_ACCESS_KEY="..."
AWS_REGION="us-east-1"
S3_BUCKET_NAME="your-bucket"

# Option B: Local MinIO (uncomment this line)
# S3_ENDPOINT_URL="http://minio:9000"
```

```bash
# services/prompt/.env
DATABASE_URL="postgresql+asyncpg://postgres:password@postgres:5432/prompt_db"
# (same AWS/MinIO keys as auth)

# services/social/.env
DATABASE_URL="postgresql+asyncpg://postgres:password@postgres:5432/social_db"

# services/ai/.env
DATABASE_URL="postgresql+asyncpg://postgres:password@postgres:5432/prompt_db"
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=prompt_images
```

### 2. Build & start

```bash
docker compose up --build -d
```

> ⚠️ **First build takes 5–10 minutes.** The AI service installs PyTorch CPU + downloads CLIP model weights (~500 MB). Subsequent builds use the Docker cache.

### 3. Verify everything is healthy

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

All services should show `(healthy)`. Then open **http://localhost** in your browser.

### 4. Reset the database (wipe all data)

```bash
docker compose down -v   # removes all volumes
docker compose up -d     # fresh start with empty DBs
```

---

## 🗂️ Project Structure

```
promptgram/
├── docker-compose.yaml          ← Orchestrates all 9 containers
├── nginx/nginx.conf             ← API gateway path routing
├── scripts/init-dbs.sql         ← Creates auth_db, prompt_db, social_db on first run
│
├── frontend/                    ← React SPA (Vite + vanilla CSS)
│   ├── src/
│   │   ├── App.jsx              ← Router + AppLayout (Sidebar + RightPanel)
│   │   ├── index.css            ← Design system (CSS variables, all components)
│   │   ├── api/                 ← Axios client + per-service modules
│   │   │   ├── client.js        ← Base URL /api, JWT interceptor, 401 handler
│   │   │   ├── auth.js
│   │   │   ├── prompts.js
│   │   │   └── social.js
│   │   ├── context/
│   │   │   ├── AuthContext.jsx  ← JWT decode, login/logout
│   │   │   └── ThemeContext.jsx ← Dark/light toggle, localStorage persist
│   │   ├── components/
│   │   │   ├── Sidebar.jsx      ← Navigation, user avatar, AI badge
│   │   │   ├── RightPanel.jsx   ← Stats, trending tags, suggested users
│   │   │   ├── PromptCard.jsx   ← Feed card: image, author, prompt, actions
│   │   │   ├── GoldLeaves.jsx   ← Animated SVG particle system (dark mode)
│   │   │   └── ThemeToggle.jsx
│   │   └── pages/
│   │       ├── FeedPage.jsx     ← Recent / Trending tabs, masonry grid
│   │       ├── PromptDetailPage.jsx ← Full prompt view, comments, actions
│   │       ├── UploadPage.jsx   ← Drag-drop image upload + prompt form
│   │       ├── SearchPage.jsx   ← Semantic search via CLIP
│   │       ├── ProfilePage.jsx  ← User prompts + follow stats
│   │       ├── LoginPage.jsx
│   │       └── SignupPage.jsx
│   └── vite.config.js           ← Dev proxy: /api → http://localhost:80
│
└── services/
    ├── auth/                    ← Auth microservice (port 8001)
    │   ├── main.py
    │   ├── models/user.py
    │   ├── schemas/auth.py
    │   ├── routers/auth.py      ← /signup /login /me /logout /users/{id}
    │   ├── services/auth_service.py
    │   └── dependencies/auth.py ← JWT validation middleware
    │
    ├── prompt/                  ← Prompt microservice (port 8002)
    │   ├── main.py
    │   ├── models/ (prompt.py, image.py)
    │   ├── schemas/ (prompt.py, image.py)
    │   ├── routers/
    │   │   ├── prompts.py       ← CRUD + trending; enriches with username + thumbnail
    │   │   └── images.py        ← Upload → S3 → trigger AI pipeline (BackgroundTask)
    │   ├── services/prompt_service.py  ← Joins images table, resolves usernames
    │   └── s3_client.py         ← boto3 async wrapper (S3 or MinIO)
    │
    ├── social/                  ← Social microservice (port 8003)
    │   ├── main.py
    │   ├── models/social.py     ← Like, Comment, Follow, Collection models
    │   ├── schemas/
    │   └── routers/
    │       ├── social.py        ← /like, /comment, /follow
    │       ├── collections.py   ← Named prompt collections
    │       └── users.py         ← Proxies to auth/prompt services
    │
    └── ai/                      ← AI microservice (port 8004)
        ├── main.py              ← Loads models at startup (lifespan)
        ├── model_manager.py     ← CLIP + MobileNetV3 + NudeNet singletons
        ├── qdrant_client_helper.py
        └── routers/
            ├── embed.py         ← CLIP ViT-B/32 image → 512D vector → Qdrant
            ├── search.py        ← Text query → CLIP → Qdrant cosine search
            ├── classify.py      ← MobileNetV3 ImageNet → auto-tags + quality score
            ├── moderate.py      ← NudeNet NSFW detection (ONNX)
            └── pipeline.py      ← Orchestrates: moderate → classify → embed
```

---

## 🔌 API Reference

All routes are accessed through the Nginx gateway at **http://localhost** (port 80).

### Auth — `/api/auth/`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/signup` | ❌ | Register → returns JWT |
| `POST` | `/api/auth/login` | ❌ | Login (OAuth2 form-data) → returns JWT |
| `GET` | `/api/auth/me` | ✅ | Current user profile |
| `POST` | `/api/auth/logout` | ✅ | Blacklist token in Redis (24h TTL) |
| `GET` | `/api/auth/users/{id}` | ❌ | Public user lookup (used inter-service) |

### Prompts — `/api/prompts/`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/prompts/` | ✅ | Create prompt |
| `GET` | `/api/prompts/` | ❌ | List prompts — returns `username` + `thumbnail_url` enriched |
| `GET` | `/api/prompts/trending` | ❌ | Trending feed (Redis cached 5 min) |
| `GET` | `/api/prompts/{id}` | ❌ | Get prompt + increment view count |
| `PATCH` | `/api/prompts/{id}` | ✅ | Update (owner only) |
| `DELETE` | `/api/prompts/{id}` | ✅ | Delete (owner only) |

### Images — `/api/images/`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/images/upload?prompt_id=` | ✅ | Upload image → S3 → thumbnail → AI pipeline |
| `GET` | `/api/images/prompt/{id}` | ❌ | All images for a prompt |
| `DELETE` | `/api/images/{id}` | ✅ | Delete image + S3 cleanup |

### Social — `/api/`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/like/{prompt_id}` | ✅ | Toggle like |
| `GET` | `/api/like/{prompt_id}/count` | ❌ | Like count |
| `POST` | `/api/comment/{prompt_id}` | ✅ | Add comment |
| `GET` | `/api/comment/{prompt_id}` | ❌ | Get comments |
| `DELETE` | `/api/comment/{id}` | ✅ | Delete comment (owner) |
| `POST` | `/api/follow/{user_id}` | ✅ | Toggle follow |
| `GET` | `/api/follow/{user_id}/followers` | ❌ | Follower list |
| `GET` | `/api/follow/{user_id}/following` | ❌ | Following list |
| `POST` | `/api/collections/` | ✅ | Create collection |
| `GET` | `/api/collections/my` | ✅ | My collections |
| `GET` | `/api/users/{id}` | ❌ | User profile |
| `GET` | `/api/users/{id}/prompts` | ❌ | User's prompts |

### AI — `/api/ai/`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/ai/search` | Text → CLIP → Qdrant → ranked image results |
| `POST` | `/api/ai/similar-images` | Image ID → find visually similar images |
| `POST` | `/api/ai/embed` | Embed single image into Qdrant |
| `POST` | `/api/ai/classify` | MobileNetV3 auto-tag + quality score |
| `POST` | `/api/ai/moderate` | NudeNet NSFW detection |
| `POST` | `/api/ai/pipeline/{image_id}` | Full pipeline (triggered automatically on upload) |

---

## 🤖 AI Pipeline

When an image is uploaded, the prompt service fires a non-blocking `BackgroundTask`:

```
Upload returns 201 immediately
        │
        ▼ (background)
POST /ai/pipeline/{image_id}
        │
        ├─ 1. Moderate  ──→ NudeNet NSFW check
        │                   PATCH /images/{id}/nsfw
        │
        ├─ 2. Classify  ──→ MobileNetV3 ImageNet top-5
        │                   PATCH /prompts/{id}/tags
        │                   PATCH /prompts/{id}/score
        │
        └─ 3. Embed     ──→ CLIP ViT-B/32 (512D vector)
                            Qdrant upsert
                            PATCH /images/{id}/qdrant
```

### ML Models

| Model | Size | Task |
|---|---|---|
| CLIP ViT-B/32 (`open_clip_torch`) | ~350 MB | Text & image embeddings (512D) for semantic search |
| MobileNetV3-Large (`torchvision`) | ~22 MB | ImageNet classification → auto-tags + quality score |
| NudeNet (`nudenet`) | ~80 MB | NSFW detection (ONNX runtime) |

> All models run on **CPU only** — no GPU required.

### Semantic Search Example

```bash
# Text-to-image search
curl -X POST http://localhost/api/ai/search \
  -H "Content-Type: application/json" \
  -d '{"query": "a cyberpunk cityscape at night with neon lights", "limit": 10}'

# Find visually similar images
curl -X POST http://localhost/api/ai/similar-images \
  -H "Content-Type: application/json" \
  -d '{"image_id": "<uuid>", "limit": 5}'
```

---

## 🛠️ Development

### Local dev (services outside Docker)

```bash
# Start only infrastructure
docker compose up postgres redis minio qdrant -d

# Run a service locally
cd services/auth
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Run the frontend dev server (proxies /api to localhost:80)
cd frontend
npm install
npm run dev    # http://localhost:3000
```

### Rebuild a single service

```bash
docker compose build prompt-service
docker compose up -d --no-deps prompt-service
```

### View service logs

```bash
docker logs promptgram_prompt --tail 50 -f
docker logs promptgram_ai     --tail 50 -f
```

### Database migrations (Alembic)

Each service manages its own schema independently:

```bash
# Generate a new migration
docker compose exec auth-service   alembic revision --autogenerate -m "add field"
docker compose exec prompt-service alembic revision --autogenerate -m "add field"
docker compose exec social-service alembic revision --autogenerate -m "add field"

# Apply pending migrations
docker compose exec auth-service   alembic upgrade head
docker compose exec prompt-service alembic upgrade head
docker compose exec social-service alembic upgrade head
```

---

## 🔧 Admin Interfaces

| Interface | URL | Credentials |
|---|---|---|
| **App** | http://localhost | — |
| **Auth API Docs** | http://localhost:8001/docs | — |
| **Prompt API Docs** | http://localhost:8002/docs | — |
| **Social API Docs** | http://localhost:8003/docs | — |
| **AI API Docs** | http://localhost:8004/docs | — |
| **MinIO Console** | http://localhost:9001 | `minioadmin` / `minioadmin` |
| **Qdrant Dashboard** | http://localhost:6334/dashboard | — |

---

## 🧠 Key Design Decisions

| Decision | Rationale |
|---|---|
| JWT validated locally in each service | No auth network hop per request — shared `JWT_SECRET` |
| No cross-service DB foreign keys | Services own their data; cross-references are plain UUIDs |
| One Postgres instance, 3 databases | Isolation without running multiple Postgres containers |
| AI pipeline as BackgroundTask | Upload returns immediately; AI processing is async |
| Prompt list enriched with `username` + `thumbnail_url` | Single API call per card — no N+1 from frontend |
| Redis trending cache (5 min TTL) | Score = `views×0.4 + downloads×0.4 + COALESCE(score,0)×0.2` |
| CPU-only PyTorch | Runs on any VPS or laptop — no GPU needed |
| Qdrant for vector storage | Persistent, fast cosine similarity, self-hosted |

---

## 🗃️ Tech Stack

**Frontend**
- React 18 + Vite
- React Router v6
- Vanilla CSS (CSS custom properties design system)
- Lucide React (icons)
- Axios

**Backend**
- FastAPI + Uvicorn (async)
- SQLAlchemy 2.0 (async) + Alembic
- asyncpg (PostgreSQL driver)
- redis-py (async)
- httpx (inter-service calls)
- python-jose (JWT)
- boto3 (S3 / MinIO)
- Pillow (thumbnail generation)

**AI**
- open_clip_torch (CLIP ViT-B/32)
- torchvision (MobileNetV3)
- nudenet (NSFW detection, ONNX)
- qdrant-client

**Infrastructure**
- Docker Compose
- Nginx
- PostgreSQL 16
- Redis 7
- MinIO
- Qdrant v1.9
