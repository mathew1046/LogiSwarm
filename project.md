# LogiSwarm

## Project Context

**What:** A geo-aware swarm of AI agents that continuously monitors global supply chain routes, detects disruptions before they cascade, and automatically recommends or executes reroutes.

**Why it exists:** Current logistics systems are reactive — teams learn about disruptions after shipments are already delayed. LogiSwarm flips this by giving each geographic region its own always-on AI agent that watches live feeds, reasons over historical memory, and communicates with neighboring agents when risk signals emerge.

**Core mechanic:** Each geo-agent runs a perceive → reason → act loop. It ingests live data (AIS vessel positions, weather, port sensors, carrier APIs, geopolitical news), detects statistical anomalies against rolling baselines, queries its episodic memory (Zep) for analogous past disruptions, calls Claude to reason over the combined context, and either broadcasts alerts to neighbors or fires reroute actions — all before a human notices anything is wrong.

**Stack:** Python 3.11 · FastAPI · Vue 3 · TimescaleDB · PostgreSQL · Redis · Zep Cloud · Anthropic Claude API · Leaflet.js · D3.js · Docker

**Deployment:** Single VPS (dev) → AWS ap-south-1 (prod). Agents are lightweight async Python coroutines — all compute cost is in LLM API calls and managed DBs.

**Agent topology:**
- Tier 1 (8 agents): SE Asia, Europe, Gulf/Suez, N. America, China/EA, S. Asia, Latin America, Africa
- Tier 2 (40–80): Port clusters and chokepoints (added later)
- Tier 3 (200–500): Individual port/airport nodes (scale phase)

**Key differentiators vs. a dashboard:** Agents talk to each other (Redis pub/sub). A Suez closure detected by Agent #03 automatically updates SE Asia and Europe agents' risk context within one cycle. The orchestrator computes cascade scores across the full trade graph. Decisions are logged with full audit trails and fed back into agent memory.

**Reference:** Architecture inspired by MiroFish swarm intelligence engine. Plan: `PLAN.md` (100 tasks, 8 phases).

---

## Implementation Status

**Overall:** 72/100 tasks complete · Phase 7 complete ✅

| Phase | Tasks | Status | Complete |
|---|---|---|---|
| 0 — Foundation | 001–006 | ✅ Complete | 6/6 |
| 1 — Data Ingestion | 007–013 | ✅ Complete | 7/7 |
| 2 — Geo-Agent Core | 014–025 | ✅ Complete | 12/12 |
| 3 — Orchestration | 026–031 | ✅ Complete | 6/6 |
| 4 — Action Layer | 032–036 | ✅ Complete | 5/5 |
| 5 — Backend API | 037–043 | ✅ Complete | 7/7 |
| 6 — Frontend | 044–058 | ✅ Complete | 15/15 |
| 7 — Polish | 059–072 | ✅ Complete | 14/14 |
| 8 — Advanced | 073–100 | 🔲 Not started | 0/28 |

**Last completed task:** Task 072 — Seed Data & Demo Scenario
**Next task:** Task 073 — Phase 8 Advanced features
**Blockers:** None
