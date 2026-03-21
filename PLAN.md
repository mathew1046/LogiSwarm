# Smart Supply Chains — Geo-Aware Swarm Intelligence
## Project Build Plan

> Inspired by MiroFish's multi-agent simulation architecture, adapted for real-time logistics intelligence.
> Stack: Python (FastAPI) · Vue 3 · PostgreSQL · Redis · TimescaleDB · Zep Cloud · Anthropic Claude API

---

## Architecture Overview

```
Data Feeds → Geo-Agents (LLM-powered, geo-bound) → Swarm Orchestrator → Route Optimizer → Action Layer → Ops Dashboard
```

Each geo-agent owns a region, holds episodic memory (Zep), watches live feeds, and communicates via Redis pub/sub. The orchestrator aggregates signals, scores cascade risk, and fires reroutes or alerts.

---

## Phase 0 — Project Foundation

---

### Task 001 — Repository & Monorepo Setup
**What:** Initialize the monorepo with `backend/` (FastAPI) and `frontend/` (Vue 3 + Vite) folders. Add `.gitignore`, `README.md`, `.env.example`, and `pyproject.toml`.
**How:**
- `mkdir -p backend frontend`
- `cd backend && uv init` (Python ≥ 3.11)
- `cd frontend && npm create vite@latest . -- --template vue`
- Add root `package.json` with `dev`, `setup:all`, `setup:backend` scripts (mirror MiroFish pattern)
- `.env.example` must include: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME`, `ZEP_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `TIMESCALE_URL`

```
commit: "Initial commit: monorepo scaffold with FastAPI backend and Vue 3 frontend"
```

---

### Task 002 — Docker Compose for Local Dev
**What:** `docker-compose.yml` that spins up PostgreSQL, TimescaleDB, Redis, and the app services.
**How:**
- Services: `postgres` (TimescaleDB image), `redis`, `backend` (mounts `./backend`), `frontend` (mounts `./frontend`)
- Add `.dockerignore`
- Add health checks on DB and Redis before backend starts
- Document ports: frontend `3000`, backend `5001`, postgres `5432`, redis `6379`

```
commit: "feat(docker): add docker-compose with TimescaleDB, Redis, backend and frontend services"
```

---

### Task 003 — Backend Base: FastAPI App + Logging
**What:** Create `backend/app/main.py` with FastAPI instance, CORS, lifespan handler, and structured logging.
**How:**
- Use `loguru` for logging
- On startup: print all registered routes (MiroFish pattern)
- CORS: allow all origins in dev, env-configurable in prod
- Add `GET /health` endpoint returning `{status: "ok", version: "0.1.0"}`
- Add `MaxTokensWarningFilter` to suppress noisy LLM warnings in logs

```
commit: "feat(backend): initialize FastAPI app with structured logging and health endpoint"
```

---

### Task 004 — Database Models & Migrations (Alembic)
**What:** Define SQLAlchemy models for core entities. Set up Alembic for migrations.
**How:**
- Models: `GeoRegion`, `ShipmentRecord`, `DisruptionEvent`, `RouteRecommendation`, `AgentEpisode`
- `GeoRegion`: id, name, bbox (polygon), risk_level, active
- `DisruptionEvent`: id, region_id, severity, signal_type, detected_at, resolved_at, cascade_score
- `AgentEpisode`: id, region_id, episode_summary (text), embedding_id (Zep ref), created_at
- Enable TimescaleDB hypertable on `DisruptionEvent` partitioned by `detected_at`

```
commit: "feat(db): define SQLAlchemy models and Alembic migrations with TimescaleDB hypertable"
```

---

### Task 005 — Redis Pub/Sub Message Bus Setup
**What:** Create `backend/app/bus/` module with publisher and subscriber helpers for inter-agent communication.
**How:**
- `publisher.py`: `async def publish(channel: str, payload: dict)`
- `subscriber.py`: `async def subscribe(channel: str, handler: Callable)`
- Channels: `agent.{region_id}.alert`, `agent.{region_id}.broadcast`, `orchestrator.cascade`, `orchestrator.reroute`
- Use `redis.asyncio` client, connection pool managed in lifespan

```
commit: "feat(bus): implement Redis pub/sub message bus for inter-agent communication"
```

---

### Task 006 — Project ID & Context Management
**What:** Every simulation/monitoring session gets a `project_id` for full traceability (mirrors MiroFish's stateful pipeline).
**How:**
- `POST /projects` → creates project record, returns `project_id`
- `GET /projects/{project_id}` → returns project metadata + status
- `GET /projects` → list all projects with status
- Store in PostgreSQL `projects` table: id, name, status (idle/running/paused/completed), created_at, config (JSONB)

```
commit: "feat(api): introduce project_id for stateful session context management"
```

---

## Phase 1 — Data Ingestion Layer

---

### Task 007 — AIS Feed Connector (Vessel Tracking)
**What:** Connector that polls AIS vessel position data for a given bounding box.
**How:**
- `backend/app/feeds/ais_connector.py`
- Use MarineTraffic or Spire public API (or mock data generator for dev)
- Output normalized schema: `{vessel_id, lat, lon, speed, heading, status, timestamp}`
- Poll interval: configurable per region (default 5 min)
- Store raw snapshots in TimescaleDB `vessel_positions` hypertable

```
commit: "feat(feeds): implement AIS vessel tracking connector with TimescaleDB storage"
```

---

### Task 008 — Weather Feed Connector (NOAA/ERA5)
**What:** Connector that fetches weather alerts and forecasts for a bounding box.
**How:**
- `backend/app/feeds/weather_connector.py`
- NOAA Weather API for US regions, Open-Meteo for global (free, no key needed)
- Normalize to: `{region_id, alert_type, severity, lat, lon, valid_from, valid_to}`
- Storm/cyclone/fog/blizzard alerts automatically tag as `HIGH_RISK` events
- Cache results in Redis with 15-min TTL

```
commit: "feat(feeds): add weather connector using Open-Meteo with severity tagging"
```

---

### Task 009 — Port Sensor Simulator (Dev Mock)
**What:** Since real port IoT sensors aren't publicly available, build a realistic mock generator.
**How:**
- `backend/app/feeds/port_simulator.py`
- Simulates: crane utilization %, vessel queue depth, gate throughput, dwell time (hours)
- Inject occasional "anomaly" spikes (e.g., crane idle for 6h, queue depth 3× baseline)
- Config: `PORT_MOCK_ENABLED=true` in `.env`
- Real path: plug in actual port authority REST APIs when available (Port of Rotterdam, MPA Singapore both have APIs)

```
commit: "feat(feeds): add port sensor mock simulator with configurable anomaly injection"
```

---

### Task 010 — Carrier API Connector (ETA / Customs)
**What:** Pull shipment ETA and customs hold data from carrier APIs.
**How:**
- `backend/app/feeds/carrier_connector.py`
- Support: Maersk Tracking API, generic REST fallback
- Normalize to: `{shipment_id, carrier, origin, destination, eta, status, delay_hours, customs_hold}`
- Parse delay signals: if `delay_hours > 24`, tag as `DELAY_ALERT`
- Retry logic: exponential backoff on 429/503

```
commit: "feat(feeds): implement carrier API connector with ETA normalization and delay tagging"
```

---

### Task 011 — GDELT Geopolitical News Connector
**What:** Pull geopolitical risk events from GDELT for a given region.
**How:**
- `backend/app/feeds/gdelt_connector.py`
- GDELT 2.0 Event API (free, no key) — query by lat/lon bounding box and event type
- Filter for supply-chain-relevant event codes: protests, sanctions, port closures, strikes
- Normalize: `{event_type, actor, region, intensity_score, date}`
- Tone score below -5 = `RISK_SIGNAL`

```
commit: "feat(feeds): add GDELT geopolitical connector with supply-chain event filtering"
```

---

### Task 012 — Unified Feed Aggregator
**What:** Single entry point that each geo-agent calls to get its current normalized event stream.
**How:**
- `backend/app/feeds/aggregator.py`
- `async def get_region_events(region_id: str, lookback_minutes: int = 60) → list[Event]`
- Merges events from all connectors, deduplicates by source + timestamp, sorts by severity
- Returns unified `Event` pydantic schema: `{source, event_type, severity, lat, lon, timestamp, raw}`

```
commit: "feat(feeds): build unified feed aggregator merging all data sources per region"
```

---

### Task 013 — Feed Health Monitoring Endpoint
**What:** API endpoint to check the health/latency of each data connector.
**How:**
- `GET /feeds/health` → returns per-connector status, last successful fetch, and event count in last hour
- If a connector has been silent for > 2× its poll interval, mark as `DEGRADED`
- Expose as dashboard widget later

```
commit: "feat(feeds): add connector health monitoring endpoint with degradation detection"
```

---

## Phase 2 — Geo-Agent Core

---

### Task 014 — GeoAgent Base Class
**What:** The core Python class that every regional agent inherits from.
**How:**
- `backend/app/agents/base_agent.py`
- Properties: `region_id`, `region_name`, `bbox`, `llm_client`, `zep_client`, `bus`
- Methods: `perceive()` → calls aggregator, `reason(events)` → calls LLM, `act(decision)` → publishes to bus
- Abstract method: `get_system_prompt() → str` (each region overrides with geo-specific context)
- Lifecycle: `start()` → `stop()` → async task via `asyncio`

```
commit: "feat(agents): implement GeoAgent base class with perceive-reason-act lifecycle"
```

---

### Task 015 — LLM Reasoning Core (Claude Integration)
**What:** The LLM call that turns perceived events into structured disruption assessments.
**How:**
- `backend/app/agents/llm_core.py`
- Use Anthropic Claude API (`claude-sonnet-4-6`)
- Input: system prompt (region context) + current events + retrieved memory episodes
- Output (structured JSON via tool use):
  ```json
  {
    "disruption_probability": 0.0-1.0,
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "affected_routes": ["string"],
    "recommended_actions": ["string"],
    "confidence": 0.0-1.0,
    "reasoning": "string"
  }
  ```
- Add `MaxTokensWarningFilter` and semaphore for rate limiting (max N concurrent LLM calls)

```
commit: "feat(agents): integrate Claude LLM reasoning core with structured JSON output"
```

---

### Task 016 — Zep Long-Term Episodic Memory
**What:** Each agent stores and retrieves disruption episodes from Zep Cloud.
**How:**
- `backend/app/agents/memory.py`
- On disruption resolved: write episode to Zep with metadata `{region_id, severity, duration_hours, resolution}`
- On new anomaly: semantic search Zep for top-3 analogous past episodes
- Format retrieved episodes into few-shot context for the LLM prompt
- Seed initial memory at agent startup from historical disruption dataset (JSON file)

```
commit: "feat(agents): add Zep episodic memory with semantic retrieval and historical seeding"
```

---

### Task 017 — Rolling Time-Series State (Short-Term Memory)
**What:** Each agent maintains a rolling window of raw metrics for statistical anomaly detection.
**How:**
- `backend/app/agents/timeseries_state.py`
- Query TimescaleDB for 7-day rolling stats per metric (mean, stddev, p95)
- Compute z-score for current value: if `z > 2.5`, flag as anomaly
- Metrics tracked: vessel queue depth, dwell time, crane utilization, weather severity score
- Expose `get_anomalies() → list[Anomaly]` for the perceive step

```
commit: "feat(agents): implement rolling time-series state with z-score anomaly detection"
```

---

### Task 018 — SE Asia Geo-Agent (Agent #01)
**What:** Instantiate the first concrete geo-agent for Southeast Asia / Strait of Malacca.
**How:**
- `backend/app/agents/regions/se_asia_agent.py`
- Bounding box: `[92.0, -10.0, 142.0, 25.0]`
- System prompt encodes: Strait of Malacca chokepoint, Port of Singapore, Port Klang, monsoon season risks (Oct-Jan), piracy risk zones
- Subscribes to AIS feed for 500+ vessels in the strait at any given time
- Historical seeding: 2021 Suez-equivalent crowding episodes, COVID port shutdowns

```
commit: "feat(agents): add SE Asia geo-agent with Malacca Strait context and AIS integration"
```

---

### Task 019 — Europe Geo-Agent (Agent #02)
**What:** Geo-agent for North Europe logistics corridor.
**How:**
- `backend/app/agents/regions/europe_agent.py`
- Bounding box: `[-10.0, 35.0, 30.0, 65.0]`
- System prompt: Port of Rotterdam (world's largest European port), Hamburg, Antwerp, Rhine river logistics, EU customs, rail freight corridors
- Watch signals: dock strikes (historically frequent), Rhine water levels (drought risk), truck driver shortages

```
commit: "feat(agents): add Europe geo-agent covering Rotterdam-Hamburg-Antwerp corridor"
```

---

### Task 020 — Gulf / Suez Geo-Agent (Agent #03)
**What:** Highest-risk geo-agent — Red Sea, Suez Canal, Persian Gulf.
**How:**
- `backend/app/agents/regions/gulf_suez_agent.py`
- Bounding box: `[32.0, 10.0, 60.0, 30.0]`
- System prompt: Suez Canal throughput (12% of global trade), Bab-el-Mandeb strait, Houthi attack zones, canal closure history (Ever Given 2021), GDELT political intensity weighting 2×
- This agent has the highest alert sensitivity — default confidence threshold lowered to 0.6 (vs 0.75 elsewhere)

```
commit: "feat(agents): add Gulf/Suez geo-agent with elevated risk sensitivity and geopolitical weighting"
```

---

### Task 021 — North America Geo-Agent (Agent #04)
**What:** Geo-agent for US intermodal and port network.
**How:**
- `backend/app/agents/regions/north_america_agent.py`
- Bounding box: `[-130.0, 20.0, -60.0, 55.0]`
- System prompt: Port of LA/Long Beach (busiest US port), Chicago rail hub, I-95 freight corridor, seasonal weather (hurricanes, blizzards), ILWU labor contract cycles
- Carrier API integration weighted heavily here (most US carriers have REST APIs)

```
commit: "feat(agents): add North America geo-agent with intermodal and port of LA focus"
```

---

### Task 022 — China / East Asia Geo-Agent (Agent #05)
**What:** Geo-agent for China manufacturing and export ports.
**How:**
- `backend/app/agents/regions/china_ea_agent.py`
- Bounding box: `[100.0, 18.0, 145.0, 45.0]`
- System prompt: Port of Shanghai (world's busiest), Ningbo-Zhoushan, Busan (transit hub), factory production cycles (CNY shutdown, Golden Week), COVID-era zero-policy legacy patterns
- Watch signals: factory sensor idle rates, export declaration volumes (customs API proxy)

```
commit: "feat(agents): add China/East Asia geo-agent covering Shanghai-Ningbo-Busan cluster"
```

---

### Task 023 — Agent Registry & Manager
**What:** Central registry that starts, stops, and queries all geo-agents.
**How:**
- `backend/app/agents/agent_manager.py`
- `AgentManager`: dict of `{region_id: GeoAgent}`
- On startup: instantiate all 5 agents, call `agent.start()`
- `GET /agents` → list all agents with their current status and last assessment
- `GET /agents/{region_id}/status` → detailed agent state
- `POST /agents/{region_id}/force-assess` → trigger immediate perception cycle

```
commit: "feat(agents): implement agent registry and manager with lifecycle control endpoints"
```

---

### Task 024 — Agent System Prompt Generator
**What:** Dynamic system prompt builder that injects live context into each agent's LLM call.
**How:**
- `backend/app/agents/prompt_builder.py`
- Base prompt: region geography, key chokepoints, historical risk patterns
- Dynamic injection: current season, recent resolved disruptions (last 30 days), active global alerts from neighboring regions
- Format retrieved Zep episodes as: `"Similar past event [DATE]: [SUMMARY] → Outcome: [RESOLUTION]"`
- Keep total prompt under 4000 tokens

```
commit: "feat(agents): add dynamic system prompt builder with live context injection"
```

---

### Task 025 — Inter-Agent Neighbor Broadcast
**What:** When an agent flags a HIGH or CRITICAL event, it broadcasts to neighboring agents.
**How:**
- Define neighbor map in config: SE Asia ↔ Gulf/Suez, SE Asia ↔ China/EA, Europe ↔ Gulf/Suez, etc.
- `agent.broadcast_to_neighbors(event: DisruptionSignal)`
- Receiving agent adds the signal to its perception context on the next reasoning cycle
- Prevents double-alerting: track broadcast IDs in Redis with 1h TTL

```
commit: "feat(agents): implement inter-agent neighbor broadcast for cross-region signal propagation"
```

---

## Phase 3 — Swarm Orchestration

---

### Task 026 — Swarm Orchestrator Core
**What:** The supervisor process that aggregates all agent signals and computes global state.
**How:**
- `backend/app/orchestrator/orchestrator.py`
- Subscribes to `agent.*.alert` on Redis
- Maintains a `GlobalRiskMap`: dict of `{region_id: AgentAssessment}`
- Every 60s: compute cross-region correlation (do multiple HIGH signals cluster on shared lanes?)
- Emit `orchestrator.cascade` event if 2+ adjacent regions flag simultaneously

```
commit: "feat(orchestrator): implement swarm orchestrator with cross-region signal aggregation"
```

---

### Task 027 — Disruption Propagation Model
**What:** Graph-based model that computes how a disruption in region A will cascade to regions B, C, D.
**How:**
- `backend/app/orchestrator/propagation_model.py`
- Build a directed logistics graph: nodes = regions, edges = major trade lanes with `volume_weight` and `dependency_score`
- When region X is disrupted: BFS/Dijkstra to find all downstream regions within 2 hops
- Compute `cascade_score` for each: `severity × volume_weight × time_decay`
- Output: `PropagationResult` with affected regions, estimated delay propagation, cascade timeline

```
commit: "feat(orchestrator): add disruption propagation model with weighted logistics graph"
```

---

### Task 028 — Route Optimization Engine
**What:** Given a disrupted primary route, find the best alternative.
**How:**
- `backend/app/orchestrator/route_optimizer.py`
- Input: `origin`, `destination`, `current_route`, `disrupted_regions: list[str]`
- Graph of global routes (preloaded from GeoJSON config): sea lanes, air freight, rail corridors
- Algorithm: modified Dijkstra excluding disrupted nodes, weighted by `cost + time + reliability`
- Return top-3 alternatives with estimated cost delta and ETA delta
- LLM post-processing: Claude summarizes the recommendation in plain English for the ops team

```
commit: "feat(orchestrator): implement route optimization engine with multi-modal alternative scoring"
```

---

### Task 029 — Cascade Risk Scoring API
**What:** Expose the propagation model output as a REST endpoint.
**How:**
- `POST /orchestrator/cascade-risk` → body: `{trigger_region, severity}` → returns full propagation result
- `GET /orchestrator/risk-map` → returns current `GlobalRiskMap` snapshot
- `GET /orchestrator/risk-map/history?hours=24` → time-series of risk map states
- Used by the dashboard to render the world risk heatmap

```
commit: "feat(orchestrator): expose cascade risk scoring and global risk map via REST API"
```

---

### Task 030 — Confidence Threshold & Escalation Logic
**What:** Define when the system acts autonomously vs. asks a human.
**How:**
- `backend/app/orchestrator/escalation.py`
- Thresholds (configurable per region): AUTO_ACT ≥ 0.85, RECOMMEND 0.60–0.84, MONITOR < 0.60
- Gulf/Suez: AUTO_ACT threshold raised to 0.90 (higher stakes, want human in loop more often)
- On AUTO_ACT: fire directly to TMS webhook + log decision
- On RECOMMEND: send structured alert to Slack/email + log
- All decisions logged to `RouteRecommendation` table with confidence, threshold, and outcome

```
commit: "feat(orchestrator): add confidence threshold escalation logic with per-region tuning"
```

---

### Task 031 — Simulation Mode (Replay Historical Events)
**What:** Replay past disruption events through the swarm to test and tune agent behavior.
**How:**
- `POST /orchestrator/simulate` → body: `{scenario: string, start_date, end_date}`
- Preloaded scenarios: `suez_2021`, `covid_port_closures_2020`, `la_port_backlog_2021`
- Feeds historical data into agents instead of live feeds
- Records agent decisions and compares to actual historical outcomes
- Returns accuracy report: detection rate, false positive rate, mean time-to-alert

```
commit: "feat(orchestrator): add simulation mode for historical event replay and agent tuning"
```

---

## Phase 4 — Action Layer

---

### Task 032 — TMS Webhook Integration (Auto-Reroute)
**What:** Fire reroute instructions directly into a Transport Management System.
**How:**
- `backend/app/actions/tms_webhook.py`
- Generic webhook client: `POST {TMS_WEBHOOK_URL}` with signed payload
- Payload schema: `{project_id, shipment_ids, new_route, reason, confidence, triggered_by}`
- Add HMAC signature for security
- Retry with exponential backoff, dead-letter queue on repeated failure
- Mock TMS endpoint in dev: `POST /mock/tms` that logs and returns 200

```
commit: "feat(actions): implement TMS webhook client for auto-reroute with HMAC signing"
```

---

### Task 033 — Slack Alert Integration
**What:** Send rich disruption alerts to a Slack channel.
**How:**
- `backend/app/actions/slack_notifier.py`
- Use Slack Block Kit for rich formatting: severity badge, affected routes, top recommendation, confidence score
- Alert levels: 🟡 MEDIUM, 🟠 HIGH, 🔴 CRITICAL (with @channel mention on CRITICAL)
- Include one-click "Accept Recommendation" button (posts back to API via Slack action webhook)
- `SLACK_WEBHOOK_URL` in `.env`

```
commit: "feat(actions): add Slack notifier with Block Kit formatting and one-click accept button"
```

---

### Task 034 — Email Alert Integration
**What:** Send HTML email alerts for disruption events.
**How:**
- `backend/app/actions/email_notifier.py`
- Use `aiosmtplib` for async sending
- Template: HTML email with severity, affected regions, route recommendations, propagation forecast
- Recipients configurable per project
- Throttle: max 1 email per 30 min per region (prevent spam on oscillating signals)

```
commit: "feat(actions): add email notifier with HTML templates and per-region throttling"
```

---

### Task 035 — Carrier Rebooking Automation
**What:** Automatically rebook cargo on alternative carriers when primary is disrupted.
**How:**
- `backend/app/actions/carrier_rebooking.py`
- Query carrier availability APIs for alternative bookings on the recommended route
- Score alternatives: `price_delta × availability × transit_time`
- On AUTO_ACT: call booking API, confirm, update `ShipmentRecord`
- On RECOMMEND: return ranked options to ops dashboard for human selection

```
commit: "feat(actions): implement carrier rebooking automation with availability scoring"
```

---

### Task 036 — Decision Audit Log
**What:** Every automated or recommended decision gets a full audit trail.
**How:**
- `backend/app/actions/audit_log.py`
- Table: `decision_log` — project_id, region_id, decision_type, confidence, input_events (JSONB), output_action (JSONB), human_override (bool), outcome, created_at
- `GET /decisions?project_id=&region_id=&limit=50` → paginated audit log
- Feedback loop: mark decision as correct/incorrect, feed back into agent memory

```
commit: "feat(actions): add decision audit log with full traceability and feedback loop"
```

---

## Phase 5 — Backend API Completeness

---

### Task 037 — Real-Time Agent Status SSE Stream
**What:** Server-Sent Events endpoint so the frontend gets live agent updates without polling.
**How:**
- `GET /agents/stream` → SSE stream
- Emits: `agent_assessment`, `disruption_detected`, `cascade_update`, `route_recommended`
- Each event: `{event_type, region_id, data, timestamp}`
- Redis subscriber bridges bus events to SSE stream

```
commit: "feat(api): add SSE stream endpoint for real-time agent status and disruption events"
```

---

### Task 038 — Shipment Tracking API
**What:** Track individual shipments through the system.
**How:**
- `POST /shipments` → register a shipment with route and carrier
- `GET /shipments/{id}` → current status, risk exposure, recommended actions
- `GET /shipments/{id}/risk` → which disrupted regions intersect this shipment's route?
- Background task: every 15 min, re-evaluate each active shipment against the current risk map

```
commit: "feat(api): add shipment tracking with real-time risk exposure evaluation"
```

---

### Task 039 — Route Registry API
**What:** CRUD API for managing the logistics route graph used by the optimizer.
**How:**
- `GET /routes` → list all known routes
- `POST /routes` → add a new route (sea lane, air, rail) with GeoJSON path and metadata
- `PUT /routes/{id}/disable` → mark route as disrupted (manual override)
- Preloaded: top 50 global shipping lanes as seed data

```
commit: "feat(api): add route registry with GeoJSON support and manual disruption override"
```

---

### Task 040 — Agent Configuration API
**What:** Let operators tune agent parameters without restarting the server.
**How:**
- `GET /agents/{region_id}/config` → current thresholds, poll intervals, memory settings
- `PUT /agents/{region_id}/config` → update config, hot-reload agent
- Config params: `poll_interval_seconds`, `confidence_threshold`, `auto_act_enabled`, `broadcast_to_neighbors`
- Changes persisted to DB and take effect on next agent cycle

```
commit: "feat(api): add agent configuration API with hot-reload support"
```

---

### Task 041 — Report Generation (Post-Disruption Analysis)
**What:** After a disruption resolves, generate a structured analysis report (mirrors MiroFish's ReportAgent).
**How:**
- `backend/app/report/report_agent.py`
- Triggered when `DisruptionEvent.resolved_at` is set
- ReportAgent tools: `query_disruption_timeline`, `get_affected_shipments`, `get_decisions_taken`, `get_cascade_impact`, `fetch_agent_memory`
- Output: markdown report with sections: Executive Summary, Timeline, Cascade Analysis, Decisions Taken, Lessons Learned
- Max 5 tool calls per section, enforce diversity (no repeated tools)

```
commit: "feat(report): implement ReportAgent for automated post-disruption analysis generation"
```

---

### Task 042 — Report Storage & Retrieval API
**What:** Store and serve generated reports.
**How:**
- Table: `reports` — id, project_id, disruption_id, content (text), generated_at, report_type
- `GET /reports?project_id=` → list reports
- `GET /reports/{id}` → full report content
- `GET /reports/latest?project_id=` → latest report (mirrors MiroFish's `get_latest_report_id`)
- Reports support markdown rendering in frontend

```
commit: "feat(report): add report storage and retrieval API with markdown support"
```

---

### Task 043 — Startup Logging & API Endpoint Display
**What:** On backend startup, print all registered routes in a clean table (MiroFish pattern).
**How:**
- Hook into FastAPI's startup event
- Print: method, path, description for every route
- Color-code by method: GET=green, POST=blue, PUT=yellow, DELETE=red
- Also log: connected DB status, Redis status, Zep status, number of agents started

```
commit: "feat(backend): add startup logging with route table and dependency health display"
```

---

## Phase 6 — Frontend Foundation

---

### Task 044 — Vue 3 App Shell + Router
**What:** Base Vue 3 app with Vue Router and Pinia state management.
**How:**
- Routes: `/` (Home), `/projects` (Dashboard), `/projects/:id` (Main View), `/projects/:id/map` (Risk Map), `/projects/:id/reports` (Reports), `/projects/:id/interact` (Interact)
- Pinia stores: `useProjectStore`, `useAgentStore`, `useAlertStore`
- Global layout: sidebar nav + top bar with project selector

```
commit: "feat(frontend): initialize Vue 3 app with Vue Router, Pinia, and global layout"
```

---

### Task 045 — Home Page
**What:** Landing page explaining the system and allowing project creation.
**How:**
- Hero section: system name, tagline, "New Project" CTA
- Features grid: 5 cards (Geo Agents, Live Feeds, Propagation Model, Auto-Reroute, Reports)
- Recent projects list (fetched from API)
- Smooth scroll, clean typography (Noto Sans / system font stack)
- Version badge in corner

```
commit: "feat(frontend): build home page with hero, feature cards, and recent projects list"
```

---

### Task 046 — Project Creation Flow (Step 1)
**What:** Multi-step wizard to configure a new monitoring project.
**How:**
- Step 1: Name project, select monitoring regions (checkbox list of 5 geo-agents)
- Step 2: Configure thresholds per region (slider: 0.5–0.95)
- Step 3: Add shipments to track (import CSV or manual entry)
- Step 4: Review & launch
- On submit: `POST /projects`, then navigate to `/projects/:id`

```
commit: "feat(frontend): add multi-step project creation wizard with region and shipment config"
```

---

### Task 047 — Main View Layout (Step-Based Workflow)
**What:** The main project view with workflow step indicators (mirrors MiroFish's MainView).
**How:**
- Step pills: Setup → Monitoring → Disruption → Response → Report
- Each step has its own panel component
- Sticky step indicator at top, scrollable content below
- Active step highlighted, completed steps checkmarked

```
commit: "feat(frontend): implement main view with step-based workflow indicator"
```

---

### Task 048 — Agent Status Panel
**What:** Live view of all geo-agents and their current assessments.
**How:**
- Card grid: one card per region
- Each card: region name, current risk level (color-coded), last assessment time, top signal, confidence score
- Color coding: green (LOW), yellow (MEDIUM), orange (HIGH), red (CRITICAL)
- Cards pulse/animate when a new assessment arrives via SSE
- Click card → expand to show full reasoning and top 3 recommended actions

```
commit: "feat(frontend): add agent status panel with live SSE-driven risk level cards"
```

---

### Task 049 — World Risk Map (Leaflet.js)
**What:** Interactive world map showing geo-agent risk levels as a heatmap overlay.
**How:**
- Use Leaflet.js with OpenStreetMap tiles
- Each geo-agent region rendered as a colored polygon (bbox)
- Color = current risk level, opacity = confidence score
- Active disruptions shown as pulsing markers
- Click region → side panel with agent detail
- Real-time updates via SSE → re-render overlay without full refresh

```
commit: "feat(frontend): implement world risk map with Leaflet.js and real-time overlay"
```

---

### Task 050 — Disruption Event Feed (Live Log)
**What:** Real-time scrolling log of all disruption events and agent decisions.
**How:**
- SSE-connected event list
- Each entry: timestamp, region badge, severity icon, summary, action taken
- Color-coded by severity
- Filter: by region, by severity, by action type
- Virtualized list (only render visible rows) for performance

```
commit: "feat(frontend): add real-time disruption event feed with filtering and virtualization"
```

---

### Task 051 — Route Visualization Panel
**What:** Show primary and alternative routes on the map for a selected shipment.
**How:**
- GeoJSON polylines for sea/air/rail routes
- Primary route: blue line
- Disrupted segments: red dashed line
- Recommended alternative: green line
- Side panel: cost delta, ETA delta, confidence for each alternative
- "Accept" button triggers carrier rebooking flow

```
commit: "feat(frontend): add route visualization with GeoJSON overlays and alternative comparison"
```

---

### Task 052 — Cascade Propagation Visualizer
**What:** Visual diagram showing how a disruption cascades across regions.
**How:**
- D3.js force-directed graph
- Nodes = geo-regions, edges = trade lane dependencies
- Disrupted node: red fill, pulsing
- Cascade path highlighted: orange edges with directional animation
- Node size = trade volume weight
- Edge thickness = dependency score

```
commit: "feat(frontend): implement D3.js cascade propagation visualizer with animated trade graph"
```

---

### Task 053 — Shipment Tracker Panel
**What:** View and manage tracked shipments and their risk exposure.
**How:**
- Table: shipment ID, carrier, origin → destination, ETA, risk level, recommended action
- Row click → expand to show full risk assessment and route map
- Bulk import: CSV upload with validation
- Filter/sort by risk level, ETA, carrier
- Export: download current risk report as CSV

```
commit: "feat(frontend): add shipment tracker panel with bulk import and risk exposure display"
```

---

### Task 054 — Alert Notification Center
**What:** In-app notification center for all alerts.
**How:**
- Bell icon in top bar with unread count badge
- Slide-out panel: list of recent alerts with severity and region
- Each alert: expandable with full details and action buttons (Accept / Dismiss / Escalate)
- Persist read/unread state in localStorage
- Link to full decision log for each alert

```
commit: "feat(frontend): add in-app alert notification center with read/unread state"
```

---

### Task 055 — Agent Configuration Panel
**What:** UI for tuning agent parameters per region.
**How:**
- Form per region: poll interval (slider), confidence threshold (slider), auto-act toggle, neighbor broadcast toggle
- Live preview: "At this threshold, X of the last 100 signals would have triggered auto-action"
- Save → `PUT /agents/{region_id}/config`
- Reset to defaults button

```
commit: "feat(frontend): build agent configuration panel with live threshold preview"
```

---

### Task 056 — Report Viewer (Step 4)
**What:** Render post-disruption analysis reports with good typography and navigation.
**How:**
- Markdown → HTML rendering (use `marked.js`)
- Section navigation: TOC sidebar, scroll-spy active section
- Section numbering
- Timeline section rendered as visual timeline (not just text)
- Print/export to PDF button
- Custom scrollbar styling

```
commit: "feat(frontend): implement report viewer with markdown rendering and section navigation"
```

---

### Task 057 — Interactive Q&A with Report Agent (Step 5)
**What:** Chat interface to ask follow-up questions about a disruption report.
**How:**
- `POST /reports/{id}/chat` → sends user message to ReportAgent with report context
- Chat bubbles: user (right), agent (left with agent avatar)
- ReportAgent tool calls shown as collapsible cards in the chat
- Typing indicator while agent is responding
- Chat history cached in Pinia store

```
commit: "feat(frontend): add interactive Q&A chat interface for ReportAgent follow-up questions"
```

---

### Task 058 — History Database (Past Projects)
**What:** Gallery of past monitoring projects and their outcomes (mirrors MiroFish's HistoryDatabase).
**How:**
- Card grid of past projects
- Each card: project name, date range, regions monitored, disruptions detected, reports generated
- Expandable card with project summary and link to reports
- Animate card expansion with debounce and animation lock (no jank)
- Modal for full project detail

```
commit: "feat(frontend): add history database with expandable project cards and detail modal"
```

---

## Phase 7 — Polish & Production Readiness

---

### Task 059 — Frontend Dark Mode
**What:** System-preference-aware dark mode across the full frontend.
**How:**
- Use CSS variables for all colors (already required by architecture)
- Toggle in top bar
- Persist preference in localStorage
- Map colors update with dark mode (Leaflet tile layer switches to dark variant)
- Test all components in both modes

```
commit: "style(frontend): implement full dark mode with CSS variables and user preference persistence"
```

---

### Task 060 — UTF-8 & Cross-Platform Encoding
**What:** Ensure backend works on Windows (encoding issues with multiprocessing).
**How:**
- Add `PYTHONIOENCODING=utf-8` in `.env.example`
- Set stdout encoding explicitly in `main.py`, `simulation_runner.py`
- Add `# -*- coding: utf-8 -*-` headers to files with non-ASCII content
- Test on Windows runner in CI

```
commit: "fix(backend): add UTF-8 encoding support for cross-platform Windows compatibility"
```

---

### Task 061 — Signal Handling & Graceful Shutdown
**What:** Clean shutdown of all agents and connections on SIGTERM/SIGINT.
**How:**
- Register `SIGTERM`, `SIGINT`, `SIGHUP` (Unix) handlers in `main.py`
- On signal: `agent_manager.stop_all()` → flush Zep writes → close DB pool → close Redis
- Log shutdown sequence with timing
- Timeout: if any step takes > 10s, force kill

```
commit: "fix(backend): add signal handling for graceful shutdown of agents and connections"
```

---

### Task 062 — Rate Limiting & LLM Semaphore
**What:** Prevent runaway LLM costs and API throttling.
**How:**
- Global semaphore: max 5 concurrent LLM calls across all agents
- Per-agent: min 60s between reasoning cycles (configurable)
- OpenRouter/Anthropic budget guard: if daily spend > threshold, switch to smaller model
- Log all LLM calls: tokens in, tokens out, cost estimate, latency

```
commit: "feat(backend): add LLM semaphore and rate limiting with cost guard and usage logging"
```

---

### Task 063 — Non-UTF-8 File Parser Fix
**What:** Handle files with non-standard encodings in data ingestion.
**How:**
- Use `chardet` for automatic encoding detection before parsing
- Fallback chain: UTF-8 → detected encoding → latin-1 (always succeeds)
- Log encoding used for each file
- Add test with GB2312-encoded Chinese port data file

```
commit: "fix(feeds): handle non-UTF-8 encoded data files with automatic encoding detection"
```

---

### Task 064 — Environment Variable Override Support
**What:** Allow `.env` values to be overridden by actual environment variables (for deployment).
**How:**
- Use `python-dotenv` with `override=False` so real env vars take precedence over `.env`
- Document all env vars in `.env.example` with comments explaining each
- Add startup validation: if required vars are missing, print clear error and exit

```
commit: "fix(config): environment variables take precedence over .env for deployment flexibility"
```

---

### Task 065 — Pagination for All List Endpoints
**What:** Add cursor-based pagination to all list endpoints.
**How:**
- Standard params: `?limit=20&cursor=<last_id>`
- Response envelope: `{data: [...], next_cursor: string|null, total: int}`
- Apply to: `/agents`, `/shipments`, `/decisions`, `/reports`, `/projects`
- Frontend: infinite scroll or "Load More" buttons

```
commit: "feat(api): implement cursor-based pagination for all list endpoints"
```

---

### Task 066 — API Error Handling & Validation
**What:** Consistent error responses across the entire API.
**How:**
- Global exception handler: returns `{error: string, code: string, detail: any}`
- Pydantic validation errors: 422 with field-level messages
- DB errors: 500 with sanitized message (no raw SQL in response)
- Add `X-Request-ID` header to all responses for tracing

```
commit: "feat(api): add global error handling with consistent error envelope and request IDs"
```

---

### Task 067 — Frontend Loading States & Skeletons
**What:** Every data-fetching component shows a skeleton loader, not a blank screen.
**How:**
- Skeleton components for: agent cards, shipment rows, map overlay, report sections
- Error states: retry button + error message
- Empty states: helpful prompt (e.g., "No disruptions detected in the last 24h ✓")
- Loading state for SSE: "Connecting to live feed..."

```
commit: "feat(frontend): add skeleton loaders, error states, and empty states to all panels"
```

---

### Task 068 — Mobile Responsiveness
**What:** Core dashboard usable on tablet and mobile.
**How:**
- Breakpoints: mobile < 768px, tablet 768–1024px, desktop > 1024px
- On mobile: sidebar collapses to hamburger menu, cards stack vertically, map takes full width
- Agent cards: horizontal scroll on mobile
- Minimum usable: alert feed + risk map + basic shipment view

```
commit: "style(frontend): add responsive layouts for tablet and mobile viewports"
```

---

### Task 069 — Performance: Frontend Bundle Optimization
**What:** Keep the frontend bundle fast.
**How:**
- Lazy load route components with `defineAsyncComponent`
- Tree-shake Leaflet (import only needed modules)
- Vite chunk splitting: separate vendor chunk for D3, Leaflet, Marked
- Target: < 300kb initial JS bundle (gzipped)
- Add `vite-bundle-visualizer` to analyze

```
commit: "perf(frontend): optimize bundle with lazy routes, tree-shaking, and chunk splitting"
```

---

### Task 070 — CI/CD Pipeline (GitHub Actions)
**What:** Automated testing and deployment pipeline.
**How:**
- `.github/workflows/ci.yml`:
  - On PR: lint (ruff, eslint), type-check (mypy, vue-tsc), unit tests
  - On merge to main: build Docker images, push to registry, deploy to staging
- Backend tests: pytest with httpx async client
- Frontend tests: Vitest unit tests for stores and composables
- Coverage gate: 70% minimum

```
commit: "ci: add GitHub Actions pipeline with lint, test, build, and deploy stages"
```

---

### Task 071 — README & Documentation
**What:** Comprehensive README with setup, architecture, and usage docs.
**How:**
- Sections: Overview, Architecture Diagram, Quick Start (Docker + source), Environment Variables, API Reference, Agent System, Adding New Regions
- Add badges: build status, license, Docker, version
- Architecture diagram: ASCII or embedded SVG
- Add `CONTRIBUTING.md` and `CHANGELOG.md`
- English first, structure ready for Chinese translation

```
commit: "docs(readme): add comprehensive README with architecture, setup, and API documentation"
```

---

### Task 072 — Seed Data & Demo Scenario
**What:** One-command demo that shows the full system working.
**How:**
- `scripts/seed_demo.py`:
  - Creates a demo project
  - Seeds 20 historical disruption episodes per agent into Zep
  - Activates the Suez 2021 simulation scenario
  - Adds 10 sample shipments crossing the affected region
- `npm run demo` → runs seed + starts services
- README section: "Try the Demo"

```
commit: "feat(demo): add seed script and one-command demo with Suez 2021 simulation scenario"
```

---

## Phase 8 — Advanced Features

---

### Task 073 — Multi-Modal Route Graph (Sea + Air + Rail)
**What:** Extend the route optimizer to handle multi-modal handoffs.
**How:**
- Route graph nodes: ports, airports, rail terminals
- Edges: sea lanes (speed 25kn), air lanes (speed 900km/h, 5× cost), rail corridors (speed 120km/h, 2× cost)
- Multi-modal path: find routes that combine modes, e.g., sea to Singapore → air to Frankfurt → rail to Warsaw
- Add `mode` field to route recommendations

```
commit: "feat(routes): extend optimizer with multi-modal sea/air/rail graph and handoff nodes"
```

---

### Task 074 — Predictive ETA Recalculation
**What:** When a disruption is detected, recalculate ETAs for all affected shipments proactively.
**How:**
- `backend/app/orchestrator/eta_recalculator.py`
- Triggered by any HIGH or CRITICAL disruption event
- For each shipment passing through disrupted region: compute delay hours based on cascade score
- Update `ShipmentRecord.predicted_eta` and `delay_hours`
- Notify shipper via email/Slack with new ETA

```
commit: "feat(orchestrator): add predictive ETA recalculation for affected shipments on disruption"
```

---

### Task 075 — Inventory Buffer Recommendations
**What:** When a disruption is predicted, recommend safety stock adjustments upstream.
**How:**
- `backend/app/orchestrator/inventory_advisor.py`
- Input: disruption severity, estimated duration, affected product categories
- Output: recommended inventory buffer increase % for each affected destination
- Simple model: `buffer_days = severity_multiplier × estimated_duration_days × (1 + uncertainty)`
- Expose via `GET /recommendations/inventory?disruption_id=`

```
commit: "feat(orchestrator): add inventory buffer recommendation engine for upstream planning"
```

---

### Task 076 — Agent Memory Seeding from CSV/JSON
**What:** Let operators upload historical disruption data to seed agent memories at project start.
**How:**
- `POST /agents/{region_id}/seed-memory` → accepts JSON or CSV
- CSV format: `date, event_type, severity, duration_hours, resolution_summary`
- Converts each row to a Zep episode with computed embedding
- Logs: "Seeded N episodes into agent memory for region X"
- Prevents duplicate seeding: check for existing episode by hash

```
commit: "feat(agents): add CSV/JSON memory seeding endpoint for historical disruption data upload"
```

---

### Task 077 — Dynamic Graph Memory Update
**What:** As new disruptions are resolved, automatically update each agent's knowledge graph (mirrors MiroFish's dynamic graph memory).
**How:**
- After `DisruptionEvent.resolved_at` is set: extract key entities (port name, vessel, weather type) and relationships (caused, delayed, rerouted)
- Update Zep graph with new edges
- Propagate update to neighboring agents' context on next reasoning cycle
- Log: "Graph memory updated: added N nodes, M edges for region X"

```
commit: "feat(agents): implement dynamic graph memory update on disruption resolution"
```

---

### Task 078 — Anomaly Detection Tuning API
**What:** Let operators see and adjust anomaly detection sensitivity per metric per region.
**How:**
- `GET /agents/{region_id}/anomaly-config` → current z-score thresholds per metric
- `PUT /agents/{region_id}/anomaly-config` → update thresholds
- `GET /agents/{region_id}/anomaly-history?days=30` → past anomaly detections with false positive flags
- Operators can mark past anomalies as false positives → auto-adjusts threshold (adaptive tuning)

```
commit: "feat(agents): add anomaly detection tuning API with adaptive threshold adjustment"
```

---

### Task 079 — Dual LLM Configuration (Primary + Fallback)
**What:** Support two LLM configurations — a primary (expensive/capable) and fallback (cheap/fast).
**How:**
- `.env`: `LLM_PRIMARY_*` and `LLM_FALLBACK_*` vars
- Primary used for: report generation, complex route optimization
- Fallback used for: routine perception cycles, low-confidence signals
- Auto-switch to fallback if primary API returns 429 or response > 10s
- Log which model was used for each LLM call

```
commit: "feat(backend): add dual LLM configuration with primary/fallback auto-switching"
```

---

### Task 080 — Bulk Shipment CSV Import & Validation
**What:** Import hundreds of shipments at once with validation.
**How:**
- `POST /shipments/bulk` → accepts CSV file upload
- Required columns: `shipment_id, carrier, origin_port, destination_port, eta, cargo_type`
- Validation: port codes against known port registry, date format, carrier code lookup
- Return: `{imported: N, failed: M, errors: [{row, reason}]}`
- Background task: compute initial risk exposure for all imported shipments

```
commit: "feat(api): add bulk shipment CSV import with validation and background risk assessment"
```

---

### Task 081 — Role-Based Access Control (RBAC)
**What:** Basic auth roles for the ops dashboard.
**How:**
- Roles: `viewer` (read-only), `operator` (can accept recommendations), `admin` (full config)
- JWT-based auth: `POST /auth/login` → returns token
- Middleware: check token on protected routes
- Frontend: hide action buttons for viewer role
- First user created is automatically admin

```
commit: "feat(auth): implement JWT-based RBAC with viewer/operator/admin roles"
```

---

### Task 082 — Prometheus Metrics Endpoint
**What:** Expose system metrics for monitoring.
**How:**
- `GET /metrics` → Prometheus format
- Metrics: `agent_reasoning_latency_seconds`, `disruptions_detected_total`, `auto_reroutes_total`, `llm_tokens_used_total`, `feed_events_ingested_total`
- Per-region labels on all agent metrics
- Docker Compose: add Prometheus + Grafana services in `docker-compose.monitoring.yml`

```
commit: "feat(ops): add Prometheus metrics endpoint with per-region agent and LLM metrics"
```

---

### Task 083 — WebSocket Support for High-Frequency Updates
**What:** Add WebSocket alongside SSE for lower-latency updates.
**How:**
- `WS /ws/agents/{project_id}` → real-time agent updates
- Use FastAPI's native WebSocket support
- Message types: `agent_pulse` (every 30s), `disruption_alert` (immediate), `route_update`
- Client reconnect logic in frontend with exponential backoff
- Fall back to SSE if WebSocket upgrade fails

```
commit: "feat(api): add WebSocket endpoint for low-latency agent pulse and disruption alerts"
```

---

### Task 084 — Multi-Language Report Support
**What:** Reports can be generated in English or Chinese.
**How:**
- `POST /reports/generate?lang=en|zh`
- ReportAgent system prompt includes: "Write the report in {lang}. Translate all quoted content."
- Language stored in `reports.language` column
- Frontend: language toggle in report viewer header

```
commit: "feat(report): add multi-language report generation with English and Chinese support"
```

---

### Task 085 — Offline Fallback Mode
**What:** System degrades gracefully when external feeds are unavailable.
**How:**
- If all feeds for a region return errors for > poll_interval × 3: enter DEGRADED mode
- In DEGRADED: use last known state + increase uncertainty in confidence scores
- Dashboard: show "Feed unavailable — using cached data from X minutes ago" banner
- Still run LLM reasoning on stale data with uncertainty caveat in output

```
commit: "feat(agents): add offline fallback mode with stale data reasoning and uncertainty flagging"
```

---

### Task 086 — Add 3 More Geo-Agents (Global Coverage)
**What:** Expand from 5 to 8 regions for better global coverage.
**How:**
- Agent #06: **South Asia / Indian Ocean** — Colombo, Chennai, Mumbai, Bay of Bengal cyclone belt
- Agent #07: **Latin America** — Panama Canal, Port of Santos (Brazil), Callao (Peru), Pacific coast storms
- Agent #08: **Africa / Cape of Good Hope** — Cape Town, Durban, alternative route to Suez, seasonal storms
- Each follows the same base class pattern as Tasks 018–022

```
commit: "feat(agents): add South Asia, Latin America, and Africa geo-agents for global coverage"
```

---

### Task 087 — Agent Interview Feature
**What:** Operators can "interview" a geo-agent — ask it questions about its region (mirrors MiroFish's Interview feature).
**How:**
- `POST /agents/{region_id}/interview` → `{question: string}` → agent answers using its memory + current state
- Agent uses Zep memory search + current risk map to answer
- Frontend: interview panel in agent detail view
- Responses shown with sources cited (which memory episodes were consulted)

```
commit: "feat(agents): implement agent interview feature for operator Q&A with geo-agent memory"
```

---

### Task 088 — Disruption Scenario Builder
**What:** Let analysts build custom "what-if" scenarios.
**How:**
- `POST /scenarios` → define a hypothetical: `{name, trigger_region, severity, affected_routes, duration_days}`
- Run through propagation model → get full cascade analysis
- Compare: `current_impact` vs `with_mitigation_impact` (e.g., if we reroute X% of volume)
- Save scenarios for future reference
- Frontend: scenario builder wizard

```
commit: "feat(orchestrator): add what-if scenario builder for disruption planning and mitigation analysis"
```

---

### Task 089 — Data Export & API Webhooks
**What:** Let external systems consume the platform's intelligence.
**How:**
- `GET /export/disruptions?from=&to=&format=csv|json` → bulk export
- `POST /webhooks` → register external webhook for disruption events
- Webhook payload matches the same schema as Slack alerts
- Retry failed webhooks 3× with exponential backoff
- Webhook management UI in settings page

```
commit: "feat(api): add data export and outbound webhook registration for external integrations"
```

---

### Task 090 — Automated Test Suite
**What:** Unit and integration tests for core components.
**How:**
- `backend/tests/`:
  - `test_agents.py`: agent perceive-reason-act cycle with mocked LLM and feeds
  - `test_propagation.py`: cascade model with known input → verify cascade scores
  - `test_route_optimizer.py`: optimizer returns valid alternative when primary is blocked
  - `test_feeds.py`: each connector with mocked HTTP responses
- Coverage: aim for 75%+ on orchestrator and agent modules
- Fixtures: pre-seeded DB with 30 days of disruption history

```
commit: "test: add unit and integration test suite for agents, orchestrator, and feed connectors"
```

---

### Task 091 — End-to-End Simulation Test
**What:** Full end-to-end test that exercises the complete system pipeline.
**How:**
- Scenario: inject a CRITICAL Suez closure signal into Agent #03
- Assert: Agent #03 detects and reasons correctly (HIGH severity output)
- Assert: Neighbor broadcast reaches Agent #02 (Europe) and Agent #01 (SE Asia)
- Assert: Orchestrator generates cascade risk for EU-bound shipments
- Assert: Route optimizer returns Cape of Good Hope alternative
- Assert: Slack webhook fires (mock server)
- Assert: Report generates after simulated resolution

```
commit: "test: add end-to-end simulation test for Suez closure scenario covering full pipeline"
```

---

### Task 092 — API Rate Limiting (Production Guard)
**What:** Protect the API from abuse in production.
**How:**
- Use `slowapi` (FastAPI rate limiting)
- Global: 1000 req/min per IP
- LLM-backed endpoints (`/interview`, `/reports/generate`): 10 req/min per project
- Return `Retry-After` header on 429
- Whitelist internal service IPs (Docker network)

```
commit: "feat(api): add rate limiting with slowapi and per-endpoint quotas for LLM endpoints"
```

---

### Task 093 — Frontend Analytics Dashboard (Charts)
**What:** Visual analytics on disruption history and system performance.
**How:**
- Charts (Chart.js or Recharts):
  - Disruptions per region over time (line chart)
  - Severity distribution (donut)
  - Mean time to detection (bar chart)
  - Auto-act vs. recommend vs. monitor breakdown (stacked bar)
  - Agent accuracy score over time (line)
- Date range picker: 7d / 30d / 90d / custom
- Export chart as PNG

```
commit: "feat(frontend): add analytics dashboard with disruption history and performance charts"
```

---

### Task 094 — Onboarding Tour
**What:** First-time user walkthrough.
**How:**
- Use `driver.js` (lightweight, no deps)
- Tour steps: (1) Create project → (2) View world map → (3) Agent cards → (4) Disruption feed → (5) Report viewer
- Show tour on first visit (localStorage flag)
- "Take a tour" button in top bar for repeat access
- Skip/exit at any step

```
commit: "feat(frontend): add onboarding tour with driver.js for first-time user guidance"
```

---

### Task 095 — AGPL-3.0 License & Legal Files
**What:** Proper open-source licensing (matches MiroFish's license choice).
**How:**
- Add `LICENSE` file (GNU AGPL v3)
- Add license header to all source files
- Update `package.json` and `pyproject.toml` with `"license": "AGPL-3.0"`
- Add `NOTICE` file for third-party attributions (OASIS framework, OpenStreetMap, etc.)

```
commit: "chore(legal): add AGPL-3.0 license and third-party attribution notices"
```

---

### Task 096 — Production Docker Build
**What:** Optimized multi-stage Docker images for production.
**How:**
- Backend: Python slim base, multi-stage (builder → runtime), non-root user
- Frontend: Node build stage → Nginx serve stage, gzip enabled, security headers
- `docker-compose.prod.yml`: no volume mounts, restart policies, resource limits
- Image sizes: backend < 300MB, frontend < 50MB

```
commit: "feat(docker): add multi-stage production Docker builds with Nginx frontend serving"
```

---

### Task 097 — Version Tagging & Changelog
**What:** Semantic versioning and automated changelog.
**How:**
- `CHANGELOG.md` following Keep a Changelog format
- Version in: `package.json`, `pyproject.toml`, `main.py` (startup log), frontend version badge
- Tag v0.1.0 at completion of Phase 6 (core working system)
- Tag v0.2.0 at completion of Phase 8 (advanced features)
- Use conventional commits format throughout (already enforced by this plan)

```
commit: "chore(release): tag v0.1.0 with changelog for initial working release"
```

---

### Task 098 — Performance Benchmarking
**What:** Measure and document system performance under load.
**How:**
- Use `locust` for API load testing
- Scenarios: 100 concurrent users viewing dashboard, 50 concurrent SSE connections, rapid disruption event injection
- Targets: API p95 < 200ms, SSE event delivery < 1s, LLM reasoning cycle < 8s
- Document results in `docs/performance.md`
- Add `locustfile.py` to repo

```
commit: "test(perf): add locust load tests and document performance benchmarks"
```

---

### Task 099 — Security Hardening
**What:** Production security essentials.
**How:**
- Add `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options` headers
- Sanitize all user inputs (Pydantic + explicit validation)
- Rotate JWT secret via env var (document rotation procedure)
- SQL injection: all queries via ORM (no raw SQL with user input)
- Dependency audit: `pip-audit` and `npm audit` in CI

```
commit: "security: add CSP headers, input sanitization, and dependency audit to CI pipeline"
```

---

### Task 100 — Final Integration & Live Demo Video
**What:** Full system integration test and demo recording.
**How:**
- Run complete demo: create project → activate agents → inject Red Sea disruption → watch cascade → accept reroute recommendation → generate report → interact with ReportAgent
- Record as demo video, add to README
- Screenshot gallery: world map, agent cards, cascade graph, report viewer
- Deploy to demo environment
- Publish release v0.1.0

```
commit: "release: v0.1.0 — complete smart supply chain swarm system with demo and documentation"
```

---

## Summary

| Phase | Tasks | Focus |
|---|---|---|
| 0 — Foundation | 001–006 | Repo, Docker, FastAPI, DB, Redis, Project API |
| 1 — Data Ingestion | 007–013 | AIS, Weather, Port, Carrier, GDELT, Aggregator |
| 2 — Geo-Agent Core | 014–025 | Base agent, LLM core, Memory, 5 regional agents, Manager |
| 3 — Orchestration | 026–031 | Orchestrator, Propagation, Route optimizer, Escalation, Simulation |
| 4 — Action Layer | 032–036 | TMS webhook, Slack, Email, Carrier rebooking, Audit log |
| 5 — Backend API | 037–043 | SSE, Shipments, Routes, Config, Reports, Startup logs |
| 6 — Frontend | 044–058 | App shell, Home, Wizard, Map, Visualizers, Reports, Chat |
| 7 — Polish | 059–072 | Dark mode, CI/CD, Docs, Demo, Encoding, Rate limiting |
| 8 — Advanced | 073–100 | Multi-modal routes, Inventory, RBAC, Metrics, WebSocket, Tests, Security |

**Total: 100 tasks** · Estimated: 3–4 months (solo) · 6–8 weeks (team of 3)
