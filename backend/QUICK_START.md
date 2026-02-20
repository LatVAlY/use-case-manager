# Quick Start Guide

## 1️⃣ Prerequisites Installed
- [x] Docker Desktop (for PostgreSQL, Redis, Qdrant)
- [x] Python 3.11+
- [x] Poetry (dependency manager)
- [x] Git

## 2️⃣ Environment Setup (5 min)

```bash
cd backend

# Copy environment template
cp .env.example .env

# Edit .env and add your keys:
#   OPENROUTER_API_KEY=sk-...  (sign up at openrouter.ai)
#   SECRET=your-dev-secret

nano .env
```

## 3️⃣ Start Infrastructure (2 min)

```bash
# In one terminal, start Docker containers
docker compose up -d db redis qdrant

# Wait for health checks
docker compose ps

# All should show "healthy" or "running"
```

## 4️⃣ Install Python Dependencies (3 min)

```bash
poetry install
poetry shell  # Activates virtual env
```

## 5️⃣ Run Database Migrations (1 min)

```bash
alembic upgrade head

# Output: OK [xxxxxxxxxxxxxxxx] -> success
```

## 6️⃣ Start the API (in terminal 1)

```bash
uvicorn app.main:app --reload --port 8000

# You should see:
# ✓ Uvicorn running on http://127.0.0.1:8000
# ✓ Swagger docs at http://127.0.0.1:8000/docs
```

## 7️⃣ Start Celery Worker (in terminal 2)

```bash
celery -A app.celery_app worker --loglevel=info

# You should see:
# ✓ Task queue connected to Redis
# ✓ Worker ready to accept tasks
```

## 8️⃣ Open API Documentation

```bash
open http://localhost:8000/docs
# Or visit in browser: http://localhost:8000/docs
```

---

## 🧪 Quick Test (5 min)

In Swagger UI:

### Step 1: Register
```
POST /auth/register
{
  "email": "admin@example.com",
  "password": "testpass123"
}
```
→ Note the returned `id`

### Step 2: Login
```
POST /auth/jwt/login
Body: form-data
  username: admin@example.com
  password: testpass123
```
→ Copy the `access_token` → Click "Authorize" button → Paste token

### Step 3: Create Industry
```
POST /industries
{
  "name": "Maschinenbau",
  "description": "Machine building and manufacturing"
}
```

### Step 4: Create Company
```
POST /companies
{
  "name": "TechCorp GmbH",
  "industry_id": "<copy ID from step 3>",
  "description": "Manufacturing company"
}
```

### Step 5: Upload Transcript
```
POST /transcripts
Form Data:
  file: <choose file: backend/sample_transcript.txt>
  company_id: <copy from step 4>
```
→ Note the `id` and `task_id`

### Step 6: Watch Progress (SSE)
```
GET /transcripts/{transcript_id}/events

# Open in new browser tab:
http://localhost:8000/transcripts/{id}/events
```
→ You'll see real-time progress events as JSON
→ Connection closes when done

### Step 7: View Extracted Use Cases
```
GET /use-cases?company_id=<company_id>
```
→ Should see 5-7 extracted use cases from the transcript

---

## 📊 System Architecture at a Glance

```
┌─────────────────────────────────────┐
│  FastAPI (localhost:8000)           │
│  - JWT Auth (fastapi-users)         │
│  - 45+ REST endpoints                │
│  - Role-based access (reader/        │
│    maintainer/admin)                 │
└──────────┬──────────────────────────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
PostgreSQL    Qdrant
(localhost:   (localhost:
 5432)        6333)
              Vector DB
              for searches
     
     │
     ▼
Celery Worker ←─── Redis Broker
(transcript     (localhost:
 extraction)    6379)
via LangChain
```

---

## 🔧 Troubleshooting

### Docker container not starting
```bash
docker logs <container_name>
docker compose restart
```

### Alembic migration fails
```bash
# Reset (careful!)
alembic downgrade base
alembic upgrade head
```

### Celery not processing tasks
```bash
# Check Redis connection
redis-cli ping

# Restart worker
celery -A app.celery_app worker --loglevel=debug
```

### API returns 401 (Unauthorized)
```
Click "Authorize" in /docs
Paste your JWT token (without "Bearer" prefix)
```

### Import errors
```bash
poetry install --no-cache
poetry shell
python3 -c "import app.main"
```

---

## 📚 Key URLs

| Endpoint | Purpose |
|----------|---------|
| http://localhost:8000/docs | Swagger UI (test API) |
| http://localhost:8000/health | Health check |
| http://localhost:5432 | PostgreSQL |
| http://localhost:6379 | Redis |
| http://localhost:6333 | Qdrant |
| http://localhost:8000/transcripts/{id}/events | SSE progress stream |

---

## 🚀 Next Steps

1. **Customize LLM**: Edit `app/ai/chains.py` to use your preferred model (currently set to gpt-3.5-turbo via OpenRouter)

2. **Add Embeddings**: Uncomment Qdrant upsert in `app/tasks/transcript_tasks.py` once you get embeddings from an API

3. **Frontend**: Build UI consuming the `/docs` endpoints (or use Swagger directly for now)

4. **Production**: 
   - Set `SECRET` to a strong random string
   - Use managed PostgreSQL/Redis/Qdrant
   - Deploy with Docker + Kubernetes or Cloud Run

---

## 📖 Full Documentation

- `ARCHITECTURE_PLAN.md` — Original 2-hour MVP specification
- `IMPLEMENTATION_COMPLETE.md` — What was built
- `IMPLEMENTATION_CHECKLIST.md` — Detailed checklist of all components
- `README.md` — Basic setup

---

## 💬 Questions?

Refer to ARCHITECTURE_PLAN.md for design decisions and scope (in/out).

**Happy building! 🎉**
