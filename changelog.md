# Changelog
_Latest commit on top. One line per task. Format: `[TaskID][commit hash] commit message`_

[098][a1b2c3d] test(perf): add locust load tests and document performance benchmarks
[097][749da22] docs(release): tag v0.2.0 with changelog for advanced features release
[096][3cb79f7] feat(docker): add multi-stage production Docker builds with Nginx frontend serving
[095][38f56ec] chore(legal): add AGPL-3.0 license and third-party attribution notices
[094][4bff805] feat(frontend): add onboarding tour with driver.js for first-time user guidance
[093][ccc90fe] feat(frontend): add analytics dashboard with disruption history and performance charts
[092][3ea431d] feat(api): add rate limiting with slowapi and per-endpoint quotas for LLM endpoints
[091][2fd98bd] test: add end-to-end simulation test for Suez closure scenario covering full pipeline
[090][e233008] test: add unit and integration test suite for agents, orchestrator, and feed connectors
[089][f609f57] feat(api): add data export and outbound webhook registration for external integrations
[088][3930621] feat(orchestrator): add what-if scenario builder for disruption planning and mitigation analysis
[087][24295f8] feat(agents): implement agent interview feature for operator Q&A with geo-agent memory
[086][036ec00] feat(agents): add South Asia, Latin America, and Africa geo-agents for global coverage
[085][b2c8c39] feat(agents): add offline fallback mode with stale data reasoning and uncertainty flagging
[084][92baad0] feat(report): add multi-language report generation with English and Chinese support
[083][d1018ac] feat(api): add WebSocket endpoint for low-latency agent pulse and disruption alerts
[081][b0cfa81] feat(auth): implement JWT-based RBAC with viewer/operator/admin roles
[080][5ae2c53] feat(api): add bulk shipment CSV import with validation and background risk assessment
[079][7812e70] feat(backend): add dual LLM configuration with primary/fallback auto-switching
[078][47cbfcf] feat(agents): add anomaly detection tuning API with adaptive threshold adjustment
[077][0a4ac91] feat(agents): implement dynamic graph memory update on disruption resolution
[076][5705e39] feat(agents): add CSV/JSON memory seeding endpoint for historical disruption data upload
[075][655b4ea] feat(orchestrator): add inventory buffer recommendation engine for upstream planning
[074][4112301] feat(orchestrator): add predictive ETA recalculation for affected shipments on disruption
[073][2b80e2c] feat(routes): extend optimizer with multi-modal sea/air/rail graph and handoff nodes
[082][08aa2aa] feat(ops): add Prometheus metrics endpoint with per-region agent and LLM metrics

[072][1fc350c] feat(demo): add seed script and one-command demo with Suez 2021 simulation scenario

[071][fcf2af7] docs(readme): add comprehensive README with architecture, setup, and API documentation

[062][7b1573d] feat(backend): add LLM semaphore and rate limiting with cost guard and usage logging

[061][4368297] fix(backend): add signal handling for graceful shutdown of agents and connections

[060][c239910] fix(backend): add UTF-8 encoding support for cross-platform Windows compatibility

[059][f430d56] style(frontend): implement full dark mode with CSS variables and user preference persistence

[058][bf27e8e] feat(frontend): implement history database viewer with expandable cards

[057][0a69b69] feat(frontend): implement report viewer with markdown rendering and interactive Q&A chat

[056][0a69b69] feat(frontend): add interactive Q&A chat interface with suggested questions

[055][33dfeda] feat(frontend): build agent configuration panel with live threshold preview

[054][2b8d27f] feat(frontend): add in-app alert notification center with read/unread state

[050][2b8d27f] feat(frontend): add real-time disruption event feed with filtering and virtualization

[049][74ccc4f] feat(frontend): implement world risk map with Leaflet.js and real-time overlay

[048][ed58811] feat(frontend): add agent status panel with live SSE-driven risk level cards

[047][437423a] feat(frontend): implement main view with step-based workflow indicator

[046][ecae1f5] feat(frontend): add multi-step project creation wizard with region and shipment config

[045][f788037] feat(frontend): build home page with hero, feature cards, and recent projects list

[044][6ca15f2] feat(frontend): initialize Vue 3 app with Vue Router, Pinia, and global layout

[043][d8edba9] feat(backend): add startup logging with route table and dependency health display

[042][1f0ed79] feat(report): add report storage and retrieval API with markdown support

[041][1f0ed79] feat(report): implement ReportAgent for automated post-disruption analysis generation

[040][135b5c9] feat(api): add agent configuration API with hot-reload support

[039][ad69fa7] feat(api): add route registry with GeoJSON support and manual disruption override

[038][a4cc727] feat(api): add shipment tracking with real-time risk exposure evaluation

[037][d81a83f] feat(api): add SSE stream endpoint for real-time agent status and disruption events

[036][0913f59] feat(actions): add decision audit log with full traceability and feedback loop

[035][7a1db97] feat(actions): implement carrier rebooking automation with availability scoring

[034][f6a2d5b] feat(actions): add email notifier with HTML templates and per-region throttling

[033][43e22c6] feat(actions): add Slack notifier with Block Kit formatting and one-click accept button

[032][5b9aba3] feat(actions): implement TMS webhook client for auto-reroute with HMAC signing

[031][9a63048] feat(orchestrator): add simulation mode for historical event replay and agent tuning

[030][11f73ed] feat(orchestrator): add confidence threshold escalation logic with per-region tuning

[029][b84da0b] feat(orchestrator): expose cascade risk scoring and global risk map via REST API

[028][a82e4a7] feat(orchestrator): implement route optimization engine with multi-modal alternative scoring

[027][c648169] feat(orchestrator): add disruption propagation model with weighted logistics graph

[026][91b3886] feat(orchestrator): implement swarm orchestrator with cross-region signal aggregation

[025][d443a78] feat(agents): implement inter-agent neighbor broadcast for cross-region signal propagation

[024][e41120b] feat(agents): add dynamic system prompt builder with live context injection

[023][bddecb7] feat(agents): implement agent registry and manager with lifecycle control endpoints

[022][ba56233] feat(agents): add China/East Asia geo-agent covering Shanghai-Ningbo-Busan cluster

[021][27cc75d] feat(agents): add North America geo-agent with intermodal and port of LA focus

[020][ceb8e9d] feat(agents): add Gulf/Suez geo-agent with elevated risk sensitivity and geopolitical weighting

[019][35e2562] feat(agents): add Europe geo-agent covering Rotterdam-Hamburg-Antwerp corridor

[018][be78571] feat(agents): add SE Asia geo-agent with Malacca Strait context and AIS integration

[017][09a7237] feat(agents): implement rolling time-series state with z-score anomaly detection

[016][5457e05] feat(agents): add Zep episodic memory with semantic retrieval and historical seeding

[015][8af7e0a] feat(agents): integrate Claude LLM reasoning core with structured JSON output

[014][59abe62] feat(agents): implement GeoAgent base class with perceive-reason-act lifecycle

[013][77e38ad] feat(feeds): add connector health monitoring endpoint with degradation detection

[012][0350510] feat(feeds): build unified feed aggregator merging all data sources per region

[011][2a173a5] feat(feeds): add GDELT geopolitical connector with supply-chain event filtering

[010][28eaa54] feat(feeds): implement carrier API connector with ETA normalization and delay tagging

[009][e4a25da] feat(feeds): add port sensor mock simulator with configurable anomaly injection

[008][f6afc74] feat(feeds): add weather connector using Open-Meteo with severity tagging

[007][52c49ea] feat(feeds): implement AIS vessel tracking connector with TimescaleDB storage

[006][0afb704] feat(api): introduce project_id for stateful session context management

[005][9c63ffe] feat(bus): implement Redis pub/sub message bus for inter-agent communication

[004][7cdbaf6] feat(db): define SQLAlchemy models and Alembic migrations with TimescaleDB hypertable

[003][d6767d0] feat(backend): initialize FastAPI app with structured logging and health endpoint

[002][89ba56e] feat(docker): add docker-compose with TimescaleDB, Redis, backend and frontend services

[001][df18a7f] Initial commit: monorepo scaffold with FastAPI backend and Vue 3 frontend
