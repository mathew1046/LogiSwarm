# Changelog
_Latest commit on top. One line per task. Format: `[TaskID][commit hash] commit message`_

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
