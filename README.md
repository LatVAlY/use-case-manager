<p align="center">
  <img src="https://img.shields.io/badge/AI-Powered-blue?style=for-the-badge&logo=OpenAI&logoColor=white" alt="AI Powered" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT" />
</p>

<h1 align="center">UseCase Manager</h1>

<p align="center">
  <strong>AI-powered use case extraction and management from workshop transcripts.</strong><br />
  Turn messy meeting notes and transcripts into clean, structured use cases — powered by LLMs.
</p>

<p align="center">
  <img src="backend/docs/product.png" alt="UseCase Manager Product Screenshot" width="800" />
  <br />
  <em>Visual overview of the UseCase Manager interface and extracted results</em>
</p>

<p align="center">
  <a href="https://github.com/LatVAlY/use-case-manager/stargazers"><img src="https://img.shields.io/github/stars/yourusername/usecase-manager?style=social" alt="GitHub stars" /></a>
  <a href="https://github.com/LatVAlY/use-case-manager/issues"><img src="https://img.shields.io/github/issues/yourusername/usecase-manager?style=flat-square" alt="Issues" /></a>
  <a href="https://github.com/LatVAlY/use-case-manager/blob/main/LICENSE"><img src="https://img.shields.io/github/license/yourusername/usecase-manager?style=flat-square" alt="License" /></a>
</p>

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
  - [Backend (Recommended: Docker)](#backend-recommended-docker)
  - [Backend (Manual / Development)](#backend-manual--development)
  - [Frontend](#frontend)
- [Screenshots](#screenshots)
- [Tech Stack](#tech-stack)
- [Contributing](#contributing)
- [License](#license)

## Features

- 🤖 **AI-powered extraction** — automatically identifies actors, goals, scenarios from transcripts
- 📊 **Structured use case management** — edit, version, export (Markdown, PDF, Jira-ready)
- ⚡ **Fast & modern stack** — FastAPI backend + modern frontend
- 🐳 **Easy deployment** — one-command Docker Compose
- 🔍 **Semantic search** — powered by Qdrant vector DB
- 📝 **Background processing** — Celery + Redis for long transcript analysis

## Quick Start

### Backend (Recommended: Docker)

One command to rule them all:

```bash
# Clone & enter repo
git clone https://github.com/LatVAlY/use-case-manager.git
cd usecase-manager

# Copy example env files
cp backend/.env.example backend/.env
cp client/.env.example client/.env

# ⚠️ Edit both .env files and add your OPENROUTER_API_KEY (and SECRET if needed)

# Start everything (backend + frontend + infra)
docker compose up --build
```

→ API will be at http://localhost:8000  
→ Docs / Swagger at http://localhost:8000/docs  
→ Frontend at http://localhost:3000

### Backend (Manual / Development)

```bash
cd backend

# 1. Environment
cp .env.example .env
# Edit .env → add OPENROUTER_API_KEY and SECRET

# 2. Infrastructure (in background)
docker compose up -d db redis qdrant

# 3. Dependencies
poetry install

# 4. Database migrations
alembic upgrade head

# 5. Run API server
export PROCESS=server
./run.sh

# 6. Run Celery worker (in another terminal)
export PROCESS=worker
./run.sh
```

### Frontend

```bash
cd frontend

# 1. Environment
cp .env.example .env
# Edit .env → add necessary keys if needed

# 2. Start dev server
yarn dev
# or
npm run dev
```

Open http://localhost:3000 (Vite default port)

## Screenshots


<p align="center">
  <img src="backend/docs/product.png" alt="Main Dashboard" width="600" />
  <br />
  <em>Main dashboard with extracted use cases</em>
</p>

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Alembic, Celery, Redis, Qdrant
- **AI**: OpenRouter 
- **Frontend**: Next.js + TypeScript 
- **Infra**: Docker Compose, PostgreSQL

## System Architecture

```mermaid
flowchart TD
    %% Colors & Styles
    classDef frontend fill:#e3f2fd,stroke:#2196f3,stroke-width:2px,color:#000
    classDef api fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    classDef infra fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    classDef async fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    classDef vector fill:#e0f7fa,stroke:#00bcd4,stroke-width:2px

    %% Users & Entry Points
    User[User / Team Member] -->|HTTP + JWT| Frontend
    User -->|Swagger /direct| FastAPI

    subgraph "Frontend Layer" 
        Frontend[Frontend<br>React / Vite / TS]:::frontend
    end

    %% Core API
    subgraph "Backend API Layer" 
        FastAPI[FastAPI<br>Async API + Auth<br>fastapi-users]:::api
    end

    %% Infrastructure / Datastores
    subgraph "Infrastructure & Storage" 
        Postgres[(PostgreSQL<br>SQLAlchemy 2 async<br>Users · Companies · UseCases)]:::infra
        Redis[(Redis<br>Broker + Pub/Sub<br>Progress Events)]:::infra
        Qdrant[(Qdrant<br>Vector DB<br>Hybrid dense + sparse)]:::vector
    end

    %% Async Processing
    subgraph "Background Processing" 
        Celery[Celery Workers<br>Long-running tasks]:::async
    end

    %% AI Chain
    subgraph "AI Extraction Pipeline" 
        LangChain[LangChain + OpenRouter<br>Chunk → Map → Reduce<br>Extraction Chain]:::async
    end

    %% Connections & Flows
    Frontend -->|API calls| FastAPI
    FastAPI -->|CRUD + queries| Postgres
    FastAPI -->|Trigger task| Celery
    Celery -->|Broker / Results| Redis
    Celery -->|Pub/Sub progress| Redis
    FastAPI -->|SSE subscribe| Redis
    Celery -->|Process transcript| LangChain
    LangChain -->|Extract & merge| Postgres
    LangChain -->|Embed & upsert| Qdrant
    FastAPI -->|Hybrid search| Qdrant
    FastAPI -->|Semantic + filters| Qdrant

    %% Styling groups
    class Frontend frontend
    class FastAPI api
    class Postgres,Redis infra
    class Qdrant vector
    class Celery,LangChain async

    %% Legend / Title
    Title[UseCase Manager Architecture<br>AI-powered use case extraction & management]:::api
```
