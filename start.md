# LogiSwarm Setup Guide

This guide provides detailed instructions for setting up and running LogiSwarm from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Project](#running-the-project)
5. [Development Workflow](#development-workflow)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| OS | Linux/macOS/Windows | Linux (Ubuntu 22.04+) |
| RAM | 4GB | 8GB+ |
| CPU | 2 cores | 4+ cores |
| Disk | 10GB | 20GB+ |

### Software Dependencies

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 20+ | Frontend build |
| Docker | 24+ | Containerized services |
| Docker Compose | 2.20+ | Multi-container orchestration |
| Git | 2.40+ | Version control |

### API Keys Required

| Key | Source | Required | Purpose |
|-----|--------|----------|---------|
| `LLM_API_KEY` | [Anthropic](https://console.anthropic.com/) | Yes | LLM reasoning |
| `ZEP_API_KEY` | [Zep Cloud](https://www.getzep.com/) | No | Episodic memory |

---

## Installation

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/logiswarm.git
cd logiswarm

# Verify you're on the main branch
git branch
```

### Step 2: Install System Dependencies

#### Ubuntu/Debian

```bash
# Update package lists
sudo apt update

# Install Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Log out and back in for Docker group changes
```

#### macOS

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11
brew install node@20
brew install docker docker-compose
brew install git

# Start Docker Desktop
open /Applications/Docker.app
```

#### Windows (WSL2)

```powershell
# Install WSL2
wsl --install -d Ubuntu-22.04

# Follow Ubuntu instructions inside WSL2
```

### Step 3: Install Python Dependencies

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or ~/.zshrc

# Navigate to backend directory
cd backend

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ..

# Verify installation
python -c "import fastapi; print('FastAPI installed')"
```

### Step 4: Install Node.js Dependencies

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Verify installation
npm run build
```

---

## Configuration

### Step 5: Environment Variables

Create the environment file:

```bash
cd ..  # Back to project root
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# =============================================================================
# REQUIRED VARIABLES
# =============================================================================

# Database Connection (PostgreSQL with TimescaleDB)
DATABASE_URL=postgresql+asyncpg://logiswarm:your_secure_password@localhost:5432/logiswarm

# LLM Configuration (Anthropic Claude)
LLM_API_KEY=your_anthropic_api_key_here
LLM_MODEL_NAME=claude-sonnet-4-6
LLM_BASE_URL=https://api.anthropic.com

# =============================================================================
# OPTIONAL VARIABLES (Defaults provided)
# =============================================================================

# Redis Connection
REDIS_URL=redis://localhost:6379

# Zep Cloud (Episodic Memory - Optional)
ZEP_API_KEY=your_zep_api_key_here

# JWT Authentication
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
JWT_EXPIRATION_HOURS=24

# LLM Rate Limiting
LLM_MAX_CONCURRENT=5
LLM_MIN_CYCLE_INTERVAL=60
LLM_DAILY_BUDGET_USD=10.0

# Environment
ENVIRONMENT=dev
LOG_LEVEL=INFO

# CORS (Comma-separated origins)
CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:5001

# =============================================================================
# NOTIFICATION WEBHOOKS (Optional)
# =============================================================================

# Slack Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/xxx/xxx

# Email Alerts (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=noreply@logiswarm.example.com
SMTP_USE_TLS=true

# TMS Integration
TMS_WEBHOOK_URL=https://your-tms.example.com/webhook
TMS_WEBHOOK_SECRET=your_webhook_secret
```

### Step 6: Generate JWT Secret

```bash
# Generate a secure random secret
python -c "import secrets; print(secrets.token_hex(32))"

# Copy the output and set in .env
# JWT_SECRET_KEY=<generated_secret>
```

---

## Running the Project

### Option A: Docker Compose (Recommended)

#### Start All Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Wait for services to be healthy
docker-compose ps

# Run database migrations
cd backend
alembic upgrade head
cd ..

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

#### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Vue dashboard |
| Backend API | http://localhost:5001 | FastAPI |
| API Docs | http://localhost:5001/docs | Swagger UI |
| PostgreSQL | localhost:5432 | TimescaleDB |
| Redis | localhost:6379 | Message bus |

#### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Option B: Manual Development Setup

#### Terminal 1: Database

```bash
# Start PostgreSQL with TimescaleDB
docker run -d \
  --name logiswarm-postgres \
  -e POSTGRES_USER=logiswarm \
  -e POSTGRES_PASSWORD=logiswarm \
  -e POSTGRES_DB=logiswarm \
  -p 5432:5432 \
  timescale/timescaledb:latest-pg15

# Connect and enable TimescaleDB
docker exec -it logiswarm-postgres psql -U logiswarm -d logiswarm -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Run migrations
cd backend
alembic upgrade head
```

#### Terminal 2: Redis

```bash
# Start Redis
docker run -d \
  --name logiswarm-redis \
  -p 6379:6379 \
  redis:7-alpine
```

#### Terminal 3: Backend

```bash
cd backend

# Activate virtual environment
source .venv/bin/activate

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 5001
```

#### Terminal 4: Frontend

```bash
cd frontend

# Start development server
npm run dev
```

### Production Deployment

```bash
# Build and start production containers
docker-compose -f docker-compose.prod.yml up -d --build

# Check service health
docker-compose -f docker-compose.prod.yml ps

# View resource usage
docker stats
```

---

## Development Workflow

### Database Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

### Running Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agents.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run load tests
locust -f locustfile.py --host http://localhost:5001
```

### Code Quality

```bash
# Backend linting
cd backend
ruff check app/
ruff format app/

# Frontend linting
cd frontend
npm run lint
npm run lint:fix
```

### Adding a New API Endpoint

1. Create route in `backend/app/api/`
2. Add Pydantic schemas in `backend/app/api/schemas/`
3. Register router in `backend/app/main.py`
4. Add tests in `backend/tests/`

### Adding a New Geo-Agent

1. Create agent file in `backend/app/agents/regions/`
2. Inherit from `GeoAgent` base class
3. Implement `_build_region_context()`, `_get_bbox()`, `_get_neighbors()`
4. Register in `backend/app/agents/agent_manager.py`
5. Add tests

---

## Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection
psql postgresql://logiswarm:password@localhost:5432/logiswarm

# Restart database
docker-compose restart postgres
```

#### Redis Connection Failed

```bash
# Check Redis is running
docker ps | grep redis

# Test connection
redis-cli ping

# Restart Redis
docker-compose restart redis
```

#### Migration Errors

```bash
# Reset database
cd backend
alembic downgrade base
alembic upgrade head

# Or nuke and recreate
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

#### Frontend Build Errors

```bash
cd frontend

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 20+
```

#### LLM API Errors

```bash
# Verify API key
curl -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4-6","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

### Log Locations

| Service | Log Location |
|---------|--------------|
| Backend | stdout (Docker logs) |
| Frontend | stdout (Docker logs) |
| PostgreSQL | `docker logs logiswarm-postgres` |
| Redis | `docker logs logiswarm-redis` |

### Health Checks

```bash
# Backend health
curl http://localhost:5001/health

# Database health
docker exec logiswarm-postgres pg_isready -U logiswarm

# Redis health
docker exec logiswarm-redis redis-cli ping

# All services
docker-compose ps
```

---

## Quick Reference

### Essential Commands

| Command | Purpose |
|---------|---------|
| `docker-compose up -d` | Start all services |
| `docker-compose down` | Stop all services |
| `docker-compose logs -f backend` | View backend logs |
| `alembic upgrade head` | Run migrations |
| `npm run dev` | Start frontend development |
| `uvicorn app.main:app --reload` | Start backend development |
| `pytest tests/ -v` | Run tests |

### Environment Files

| File | Purpose |
|------|---------|
| `.env` | Local development secrets |
| `.env.example` | Template for .env |
| `backend/.env` | Backend-specific overrides |

### Port Reference

| Port | Service |
|------|---------|
| 3000 | Frontend (dev) |
| 5001 | Backend API |
| 5432 | PostgreSQL |
| 6379 | Redis |

---

## Next Steps

1. Run the demo: `python backend/scripts/seed_demo.py`
2. Open http://localhost:3000
3. Create a project and watch agents activate
4. Inject a disruption and observe cascade predictions

For detailed API documentation, see http://localhost:5001/docs