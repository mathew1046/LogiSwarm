# Changelog

All notable changes to LogiSwarm will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-XX

### Added
- Phase 0-6: Foundation, Data Ingestion, Geo-Agent Core, Orchestration, Action Layer, Backend API, Frontend
- Phase 7: Polish & Production Readiness (Tasks 059-072)
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