# Promptgram

A full-stack platform for sharing, discovering, and managing AI prompts — built on a single FastAPI backend with PostgreSQL, Redis, and MinIO (S3-compatible) storage, served through an Nginx reverse proxy.

---

## Architecture

```
Browser
   └── Nginx (:80)
         ├── /        → React Frontend (coming soon)
         └── /api/    → FastAPI Backend (:8000)
                            ├── PostgreSQL 16  (primary database)
                            ├── Redis 7        (caching + rate limiting)
                            └── MinIO          (S3-compatible image storage)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Python 3.11 |
| ASGI Server | Uvicorn |
| ORM | SQLAlchemy 2 (async) + asyncpg |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Object Storage | MinIO (S3-compatible) |
| Auth | python-jose (JWT) + passlib (bcrypt) |
| File Upload | python-multipart + boto3 |
| Migrations | Alembic |
| Reverse Proxy | Nginx |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
promptgram/
├── docker-compose.yaml
├── nginx/
│   └── nginx.conf
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py
    ├── .env                  # never committed
    ├── alembic/
    │   └── versions/
    └── app/
        ├── config.py         # pydantic-settings
        ├── database.py       # async engine + session
        ├── models/
        │   ├── user.py
        │   ├── prompt.py
        │   ├── image.py
        │   ├── collection.py
        │   └── social.py     # likes, follows, comments
        ├── schemas/
        ├── routers/
        │   ├── auth.py       # /auth/*
        │   ├── prompts.py    # /prompts/*
        │   ├── image.py      # /images/*
        │   ├── social.py     # /like, /comment, /follow
        │   ├── user.py       # /users/*
        │   └── collection.py # /collections/*
        ├── dependencies/
        │   ├── auth.py       # get_current_user, require_auth
        │   └── rate_limit.py
        └── services/
```

---

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Git

### 1. Clone the repo

```bash
git clone https://github.com/yourname/promptgram.git
cd promptgram
```

### 2. Create the `.env` file

```bash
cp backend/.env.example backend/.env
```

Fill in your values:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=prompt_platform
DATABASE_URL=postgresql+asyncpg://postgres:your_password@postgres:5432/prompt_platform

# Redis
REDIS_URL=redis://redis:6379

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_password
MINIO_URL=minio:9000

# JWT
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### 3. Start all services

```bash
docker compose up -d
```

### 4. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 5. Verify

| URL | What you get |
|---|---|
| `http://localhost/api/docs` | Swagger UI |
| `http://localhost/api/health` | Health check |
| `http://localhost:9001` | MinIO console |

---

## API Endpoints

### Auth — `/api/auth`
| Method | Path | Description |
|---|---|---|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | Login, returns JWT |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Invalidate token |

### Prompts — `/api/prompts`
| Method | Path | Description |
|---|---|---|
| GET | `/prompts/` | List prompts (feed) |
| POST | `/prompts/` | Create prompt 🔒 |
| GET | `/prompts/{id}` | Get prompt detail |
| DELETE | `/prompts/{id}` | Delete prompt 🔒 |

### Images — `/api/images`
| Method | Path | Description |
|---|---|---|
| POST | `/images/upload` | Upload image (multipart) 🔒 |
| DELETE | `/images/{id}` | Delete image 🔒 |

### Social — `/api`
| Method | Path | Description |
|---|---|---|
| POST | `/like/{prompt_id}` | Toggle like 🔒 |
| POST | `/comment/{prompt_id}` | Add comment 🔒 |
| DELETE | `/comment/{id}` | Delete comment 🔒 |
| POST | `/follow/{user_id}` | Toggle follow 🔒 |

### Users — `/api/users`
| Method | Path | Description |
|---|---|---|
| GET | `/users/{id}` | Get user profile |
| GET | `/users/{id}/prompts` | Get user's prompts |
| PATCH | `/users/me` | Update own profile 🔒 |

### Collections — `/api/collections`
| Method | Path | Description |
|---|---|---|
| POST | `/collections/` | Create collection 🔒 |
| GET | `/collections/{id}` | Get collection |
| POST | `/collections/{id}/prompts/{prompt_id}` | Add prompt 🔒 |
| DELETE | `/collections/{id}/prompts/{prompt_id}` | Remove prompt 🔒 |

🔒 = requires Bearer token

---

## Docker Services

| Service | Description | Ports |
|---|---|---|
| `nginx` | Reverse proxy | 80 |
| `backend` | FastAPI app | 8000 (internal) |
| `postgres` | Primary database | 5432 |
| `redis` | Cache + rate limiting | 6379 (internal) |
| `minio` | Object storage | 9000 (internal), 9001 (console) |

---

## Development

### Rebuild after code changes

```bash
docker compose up -d --build backend
```

### Create a new migration

```bash
docker compose exec backend alembic revision --autogenerate -m "describe your change"
docker compose exec backend alembic upgrade head
```

### View logs

```bash
docker compose logs -f backend
docker compose logs -f postgres
```

### Stop everything

```bash
docker compose down
```

Stop and wipe the database:

```bash
docker compose down -v
```

---

## Roadmap

- [x] FastAPI backend with all routers
- [x] PostgreSQL + Alembic migrations
- [x] Redis caching + rate limiting
- [x] MinIO S3 image storage
- [x] JWT authentication
- [x] Nginx reverse proxy
- [ ] React frontend
- [ ] AI features (CLIP embeddings, semantic search, NSFW moderation)
- [ ] HTTPS / SSL (Certbot)
- [ ] Celery async job queue
- [ ] Gunicorn multi-worker production setup

---

## Environment Variables Reference

| Variable | Description |
|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `MINIO_URL` | MinIO internal host:port |
| `MINIO_ROOT_USER` | MinIO access key |
| `MINIO_ROOT_PASSWORD` | MinIO secret key |
| `SECRET_KEY` | JWT signing secret |
| `ALGORITHM` | JWT algorithm (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL in minutes |
| `ALLOWED_ORIGINS` | JSON array of allowed CORS origins |

---

## License

MIT