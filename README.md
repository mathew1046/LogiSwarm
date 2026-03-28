# LogiSwarm

**Geo-Aware Swarm Intelligence for Supply Chain Disruption Detection**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3-green.svg)](https://vuejs.org/)
[![Version](https://img.shields.io/badge/version-0.2.0-orange.svg)](https://github.com/your-org/logiswarm)

LogiSwarm is a geo-aware swarm of AI agents that continuously monitors global supply chain routes, detects disruptions before they cascade, and automatically recommends or executes reroutes.

## Features

- **🤖 8 Regional AI Agents**: Each geographic region has a dedicated AI agent with local expertise
- **📡 Real-time Feed Integration**: AIS vessel positions, weather data, port sensors, carrier APIs, geopolitical news
- **🧠 LLM-Powered Reasoning**: Claude-powered agents analyze disruptions and generate recommendations
- **🌊 Cascade Risk Scoring**: Multi-hop propagation model predicts downstream impacts
- **🚦 Multi-Modal Route Optimization**: Sea, air, and rail routes with automatic handoff nodes
- **🔐 JWT-Based RBAC**: Role-based access control with viewer, operator, and admin roles
- **📊 Real-time Dashboard**: World map visualization, agent status, disruption feed
- **📝 Automated Reports**: Multi-language PDF report generation with agent Q&A

## Architecture

```
Data Feeds → Geo-Agents (LLM-powered, geo-bound) → Swarm Orchestrator → Route Optimizer → Action Layer → Ops Dashboard
```

Each geo-agent owns a region, holds episodic memory (Zep), watches live feeds, and communicates via Redis pub/sub. The orchestrator aggregates signals, scores cascade risk, and fires reroutes or alerts.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+
- Anthropic API Key (for LLM reasoning)
- Zep Cloud API Key (optional, for memory)

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/logiswarm.git
cd logiswarm

# Install dependencies
npm run setup:all

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment

Edit `.env`:

```bash
# Required
DATABASE_URL=postgresql+asyncpg://logiswarm:logiswarm@localhost:5432/logiswarm
LLM_API_KEY=your_anthropic_api_key

# Optional
ZEP_API_KEY=your_zep_api_key
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

### 3. Start Services

```bash
# Start infrastructure
docker-compose up -d postgres redis

# Run database migrations
cd backend && alembic upgrade head && cd ..

# Start backend
cd backend && uvicorn app.main:app --reload --port 5001 &

# Start frontend
cd frontend && npm run dev
```

### 4. Access Dashboard

Open http://localhost:3000 in your browser.

## Demo Scenario: Suez Canal Closure

Run the built-in demo to see a complete disruption simulation:

```bash
cd backend
python scripts/seed_demo.py
```

This simulates:
1. **Red Sea/Gulf region agent detects** vessel slowdown near Suez
2. **Cascade prediction**: Impact spreads to Europe and Asia routes
3. **Route optimizer generates** alternative Cape of Good Hope paths
4. **Operator receives** recommendation and accepts reroute
5. **Systems generate** report with full audit trail

## Screenshot Gallery

| World Map | Agent Dashboard | Disruption Feed |
|-----------|----------------|-----------------|
| ![World Map](docs/screenshots/world-map.png) | ![Agents](docs/screenshots/agents.png) | ![Feed](docs/screenshots/feed.png) |

| Cascade Graph | Route Recommendation | Report Viewer |
|---------------|---------------------|---------------|
| ![Cascade](docs/screenshots/cascade.png) | ![Route](docs/screenshots/route.png) | ![Report](docs/screenshots/report.png) |

## API Documentation

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/projects` | CRUD | Project management |
| `/api/agents/{region}` | GET | Agent status |
| `/api/disruptions` | GET/POST | Disruption events |
| `/api/routes/optimize` | POST | Route optimization |
| `/api/reports` | POST | Generate reports |
| `/metrics` | GET | Prometheus metrics |

Full API documentation available at http://localhost:5001/docs

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection |
| `LLM_API_KEY` | Yes | - | Anthropic API key |
| `LLM_MODEL_NAME` | No | claude-sonnet-4-6 | Model to use |
| `ZEP_API_KEY` | No | - | Zep Cloud API key |
| `REDIS_URL` | No | redis://localhost:6379 | Redis connection |
| `JWT_SECRET_KEY` | No | random | JWT signing secret |
| `CORS_ALLOW_ORIGINS` | No | - | Allowed CORS origins |

## Deployment

### Docker Compose (Production)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

This starts:
- Backend (FastAPI + Uvicorn)
- Frontend (Nginx serving static files)
- PostgreSQL with TimescaleDB extension
- Redis for pub/sub and caching

### AWS Deployment

See [docs/deployment.md](docs/deployment.md) for AWS ECS deployment guide.

## Testing

### Unit Tests

```bash
cd backend
pytest tests/
```

### Load Testing

```bash
locust -f locustfile.py --host http://localhost:5001
```

## Security

See [docs/security.md](docs/security.md) for security measures and best practices.

## Performance

See [docs/performance.md](docs/performance.md) for benchmark results.

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Architecture inspired by swarm intelligence patterns
- Built with FastAPI, Vue 3, TimescaleDB, Redis, and Anthropic Claude

## Support

- **Issues**: https://github.com/your-org/logiswarm/issues
- **Documentation**: [docs/](docs/)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)