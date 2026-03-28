# Changelog

All notable changes to LogiSwarm will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-03-28

### Added
- **Phase 8: Advanced Features (Tasks 073-096)**
  - Multi-modal route optimizer with sea/air/rail graph and handoff nodes
  - Predictive ETA recalculation for affected shipments on disruption
  - Inventory buffer recommendation engine for upstream planning
  - CSV/JSON memory seeding endpoint for historical disruption data upload
  - Dynamic graph memory update on disruption resolution
  - Anomaly detection tuning API with adaptive threshold adjustment
  - Dual LLM configuration with primary/fallback auto-switching
  - Bulk shipment CSV import with validation and background risk assessment
  - JWT-based RBAC with viewer/operator/admin roles
  - WebSocket endpoint for low-latency agent pulse and disruption alerts
  - Multi-language report generation with English and Chinese support
  - Offline fallback mode with stale data reasoning and uncertainty flagging
  - South Asia, Latin America, and Africa geo-agents for global coverage
  - Agent interview feature for operator Q&A with geo-agent memory
  - What-if scenario builder for disruption planning and mitigation analysis
  - Data export and outbound webhook registration for external integrations
  - Unit and integration test suite for agents, orchestrator, and feed connectors
  - End-to-end simulation test for Suez closure scenario covering full pipeline
  - Rate limiting with slowapi and per-endpoint quotas for LLM endpoints
  - Analytics dashboard with disruption history and performance charts
  - Onboarding tour with driver.js for first-time user guidance
  - Prometheus metrics endpoint with per-region agent and LLM metrics

### Changed
- AGPL-3.0 license headers added to all source files
- Multi-stage production Docker builds with Nginx frontend serving

### Fixed
- Various bug fixes and performance improvements across all modules

## [0.1.0] - 2025-01-15

### Added
- **Phase 0-6: Foundation, Data Ingestion, Geo-Agent Core, Orchestration, Action Layer, Backend API, Frontend**
- **Phase 7: Polish & Production Readiness (Tasks 059-072)**
  - Frontend dark mode with CSS variables and localStorage persistence
  - UTF-8 encoding support for cross-platform compatibility
  - Graceful shutdown with signal handling
  - LLM semaphore and rate limiting with cost guard
  - Non-UTF-8 file parser with automatic encoding detection
  - Environment variable override support for deployment
  - Cursor-based pagination for list endpoints
  - Global error handling with consistent error envelope
  - Skeleton loaders, error states, and empty states
  - Mobile responsive layouts
  - Frontend bundle optimization with chunk splitting
  - CI/CD pipeline with GitHub Actions
  - Comprehensive README and documentation

### Fixed
- Windows encoding issues with UTF-8 enforcement
- Graceful shutdown of agents and connections on SIGTERM/SIGINT

### Security
- Input validation with Pydantic
- Request ID tracking for all API responses
- Environment variable precedence over .env file

## [Unreleased]

### Added
- Future improvements and features will be tracked here