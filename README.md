# LogiSwarm

**Simple multi-agent shipment routing with mocked local intelligence**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3-green.svg)](https://vuejs.org/)

LogiSwarm is now a deliberately simplified logistics demo app.

The app lets a user:
- choose a shipment **origin** and **destination** from 10 fixed places
- inspect **10 agents** on a world map
- see mocked **weather** and **news** for each agent location
- generate route options from agent-to-agent reasoning
- run a simulation that stays active until it is manually stopped
- generate a report when the simulation is stopped

## Current Product Shape

### Kept tabs
- **Home**
- **Dashboard**
- **Agents**
- **Simulation**
- **Reports**
- **Routes**

### Core model
- **1 shipment** at a time
- **10 fixed places**
- **10 fixed agents**
- **mocked weather/news** per place
- **in-memory route planning**
- **persistent simulation state** until manual stop
- **in-memory reports** generated when a simulation ends

## 10 Places / Agents

The current simplified backend uses these fixed locations:

1. Shanghai
2. Singapore
3. Mumbai
4. Dubai
5. Suez
6. Rotterdam
7. Hamburg
8. Lagos
9. Panama City
10. Los Angeles

Each place has one agent with:
- place + region metadata
- mocked weather summary
- mocked news summary
- risk score + severity
- reasoning text
- neighboring agents for route intercommunication

## Simplified Architecture

```text
Shipment Selection
  -> 10 Place Agents
  -> Route Planning
  -> Persistent Simulation State
  -> Reports
```

The simplified runtime is fully in-memory and centered around:

- `backend/app/simple_runtime.py`
- `backend/app/api/simple_app.py`

## API Surface

The current app is intentionally small.

### Core endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | backend health check |
| `/places` | GET | list the 10 available shipment places |
| `/dashboard` | GET | get current shipment, route plan, simulation state |
| `/shipments/current` | GET | get current shipment |
| `/shipments/current` | POST | set current shipment origin/destination |
| `/agents` | GET | list 10 agents with risk, weather, news, reasoning |
| `/agents/topology` | GET | get world-map nodes and agent graph edges |
| `/routes/plan` | GET | get current route plan |
| `/routes/plan` | POST | compute route options for origin/destination |
| `/simulation/start` | POST | start a simulation for the current shipment |
| `/simulation/status` | GET | fetch active/stopped simulation state |
| `/simulation/stop` | POST | manually stop simulation and create report |
| `/reports` | GET | list generated reports |
| `/auth/login` | POST | optional login |
| `/auth/register` | POST | optional register |
| `/auth/me` | GET | current auth user |

## Frontend Behavior

### Dashboard
- choose shipment origin/destination from dropdowns
- save current shipment

### Agents
- world map with one marker per agent
- click marker to inspect the agent

### Routes
- see the recommended route
- see alternative route options
- inspect inter-agent messages
- inspect each agent’s reasoning

### Simulation
- start simulation for the current shipment + recommended route
- simulation remains active until **manually stopped**
- see progress, impacted places, and live changes

### Reports
- stopping a simulation creates a new report entry

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 20+

### Start the app

```bash
docker-compose up -d
```

The current Docker setup runs:
- backend on `http://localhost:5001`
- frontend on `http://localhost:3001`

### Open the app

```text
http://localhost:3001
```

## Development

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 3001
```

### Backend

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 5001 --reload
```

## Notes

- The simplified app currently uses **in-memory state** for shipment, route plan, simulation, and reports.
- Weather and news are **mocked**, by design.
- The old project/reroute/orchestrator-heavy API surface has been removed from the active app.

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
