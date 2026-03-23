# Prism

A gamified identity-discovery and career exploration platform for Indian high school students. Students complete missions across themed worlds, chat with an AI mentor (Ray), and build a personality spectrum that maps to career recommendations — all visualized as a shareable Prism Card.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Task Queue | Celery + Redis |
| AI | Anthropic Claude API |
| Frontend | Next.js 14, React 18, Tailwind CSS, Framer Motion |
| State Management | Zustand |
| Auth | JWT + Phone OTP |

## Prerequisites

- **Python 3.11+**
- **Node.js 20+** (recommend using [nvm](https://github.com/nvm-sh/nvm))
- **PostgreSQL 16**
- **Redis 7**
- **Homebrew** (macOS)

### Install PostgreSQL and Redis (macOS)

```bash
brew install postgresql@16 redis
```

## Project Structure

```
prism/
├── backend/            # FastAPI application
│   ├── app/
│   │   ├── main.py             # App entrypoint, middleware, CORS
│   │   ├── config.py           # Settings from environment variables
│   │   ├── database.py         # SQLAlchemy async engine + session
│   │   ├── dependencies.py     # Auth guards, role checks
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── routers/            # API route handlers
│   │   ├── services/           # Business logic
│   │   └── tasks/              # Celery background jobs
│   ├── alembic/                # Database migrations
│   ├── prestart.py             # DB table initialization
│   ├── seed_db.py              # Seed data loader
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/           # Next.js application
│   ├── src/
│   │   ├── app/                # Pages (App Router)
│   │   ├── components/         # Reusable React components
│   │   ├── hooks/              # Custom hooks (useAuth, useSpectrum)
│   │   ├── lib/                # API client + utilities
│   │   └── styles/             # Tailwind config + globals
│   ├── package.json
│   └── Dockerfile
├── seed/               # Seed data (JSON)
│   ├── archetypes.json
│   ├── worlds.json
│   ├── missions.json
│   ├── tot_questions.json
│   └── careers.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## Setup (Native / No Docker)

### 1. Start PostgreSQL and Redis

```bash
brew services start postgresql@16
brew services start redis
```

Verify they are running:

```bash
brew services list
```

### 2. Create the database

```bash
# Add psql to PATH if not already available
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"

# Create database and user
createdb prism
psql prism -c "CREATE USER prism WITH PASSWORD 'prism';"
psql prism -c "GRANT ALL PRIVILEGES ON DATABASE prism TO prism;"
psql prism -c "ALTER USER prism CREATEDB;"
psql prism -c "GRANT ALL ON SCHEMA public TO prism;"
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

The defaults in `.env.example` are configured for local development. Update these values as needed:

| Variable | Default | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://prism:prism@localhost:5432/prism` | Local PostgreSQL |
| `REDIS_URL` | `redis://localhost:6379/0` | Local Redis |
| `JWT_SECRET` | `change-me-in-production` | **Change in production** |
| `CLAUDE_API_KEY` | _(empty)_ | Required for Ray AI mentor |
| `APP_ENV` | `development` | Set to `production` for prod |

### 4. Set up the backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database tables
python prestart.py

# Seed the database with archetypes, worlds, missions, careers
python seed_db.py
```

### 5. Set up the frontend

```bash
cd frontend

# Install dependencies
npm install

# Create local env file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
```

## Running the Project

You need **3 terminal sessions** (4 if you want Celery):

### Terminal 1 — Backend API

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2 — Frontend

```bash
cd frontend
npm run dev
```

### Terminal 3 — Celery Worker (optional, for background tasks)

```bash
cd backend
source venv/bin/activate
celery -A app.tasks worker --loglevel=info
```

### Terminal 4 — Celery Beat (optional, for scheduled tasks)

```bash
cd backend
source venv/bin/activate
celery -A app.tasks beat --loglevel=info
```

### Access the app

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

## Development Workflow

### Backend changes

The backend runs with `--reload`, so **any changes to Python files will auto-restart the server**. No manual restart needed.

If you modify database models:

```bash
cd backend
source venv/bin/activate

# Generate a new migration
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head
```

### Frontend changes

Next.js dev server has **hot module replacement (HMR)** built in. Changes to React components, pages, styles, and hooks are reflected instantly in the browser — no restart needed.

If you add new npm packages:

```bash
cd frontend
npm install <package-name>
# Dev server picks it up automatically
```

### When you DO need to restart

| Scenario | Action |
|----------|--------|
| Changed `.env` or `.env.local` | Restart the affected server (backend or frontend) |
| Added new Python packages | `pip install -r requirements.txt`, then restart backend |
| Changed Celery task definitions | Restart the Celery worker |
| Database schema changes | Run Alembic migration (see above) |
| Everything else | Auto-reloads, no action needed |

### Re-seeding the database

The seed script is idempotent — it skips records that already exist:

```bash
cd backend
source venv/bin/activate
python seed_db.py
```

To start fresh:

```bash
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
dropdb prism && createdb prism
psql prism -c "GRANT ALL ON SCHEMA public TO prism;"
cd backend
source venv/bin/activate
python prestart.py
python seed_db.py
```

## Stopping Services

### Stop the dev servers

Press `Ctrl+C` in each terminal session.

### Stop PostgreSQL and Redis

```bash
brew services stop postgresql@16
brew services stop redis
```

### Check service status

```bash
brew services list
```

## API Modules

| Module | Base Path | Description |
|--------|-----------|-------------|
| Auth | `/api/v1/auth` | OTP + email/password login, JWT tokens |
| Game | `/api/v1/game` | Worlds, missions, attempts, daily quests |
| Identity | `/api/v1/spectrum` | 5-dimension trait spectrum |
| AI | `/api/v1/ai` | Ray AI mentor (Claude-powered) |
| Careers | `/api/v1/careers` | Career library, recommendations, bookmarks |
| Cards | `/api/v1/cards` | Prism Card generation and sharing |
| School | `/api/v1/school` | Counsellor/admin dashboard |

## Troubleshooting

### PostgreSQL connection refused

```bash
# Check if PostgreSQL is running
brew services list

# Restart it
brew services restart postgresql@16
```

### Redis connection refused

```bash
brew services restart redis
```

### `psql: command not found`

```bash
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
```

Add this line to your `~/.zshrc` to make it permanent:

```bash
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Port already in use

```bash
# Find and kill the process on a port (e.g., 8000)
lsof -ti:8000 | xargs kill -9

# Or for frontend port
lsof -ti:3000 | xargs kill -9
```

### Python virtual environment issues

```bash
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
