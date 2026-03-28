# Performance Benchmarks

This document describes the performance characteristics and load testing results for LogiSwarm.

## Test Environment

- **Hardware**: AWS t3.medium (2 vCPU, 4GB RAM)
- **Database**: TimescaleDB on PostgreSQL 15
- **Redis**: Redis 7 Alpine
- **Backend**: FastAPI with Uvicorn, Python 3.11
- **Frontend**: Vue 3 with Vite, served via Nginx

## Performance Targets

| Metric | Target | Description |
|--------|--------|-------------|
| API Response (p95) | < 200ms | 95th percentile response time for API endpoints |
| SSE Event Delivery | < 1s | Time from event generation to client delivery |
| LLM Reasoning Cycle | < 8s | Agent perceive-reason-act cycle time |
| Concurrent Users | 100+ | Simultaneous dashboard viewers |
| SSE Connections | 50+ | Concurrent SSE streams |

## Load Testing with Locust

### Installation

```bash
pip install locust
```

### Running Tests

```bash
# Run all scenarios
locust -f locustfile.py --host http://localhost:5001

# Run specific user class
locust -f locustfile.py LogiSwarmUser --host http://localhost:5001

# Headless mode (CI/CD)
locust -f locustfile.py --host http://localhost:5001 --users 100 --spawn-rate 10 -t 5m --headless
```

### Test Scenarios

#### Scenario 1: Dashboard Viewers (100 concurrent users)

```bash
locust -f locustfile.py LogiSwarmUser --host http://localhost:5001 \
    --users 100 --spawn-rate 10 -t 5m --headless
```

**Expected Results:**
| Endpoint | p50 | p95 | p99 | RPS |
|----------|-----|-----|-----|-----|
| /health | 5ms | 15ms | 30ms | 500+ |
| /api/projects | 10ms | 50ms | 100ms | 100+ |
| /api/projects/{id}/agents | 20ms | 80ms | 150ms | 50+ |
| /api/projects/{id}/feeds/events | 30ms | 100ms | 200ms | 30+ |

#### Scenario 2: SSE Connections (50 concurrent streams)

```bash
locust -f locustfile.py SSEConnectionUser --host http://localhost:5001 \
    --users 50 --spawn-rate 5 -t 10m --headless
```

**Expected Results:**
- 50 concurrent connections maintained
- Event delivery latency < 1s
- No connection drops during test

#### Scenario 3: Disruption Injection (Stress Test)

```bash
locust -f locustfile.py DisruptionSpamUser --host http://localhost:5001 \
    --users 20 --spawn-rate 5 -t 3m --headless
```

**Expected Results:**
- Graceful handling under load
- Queue-based processing maintains stability
- Error rate < 1%

## Benchmark Results

### API Performance (v0.2.0)

| Endpoint | Method | p50 | p95 | p99 | Notes |
|----------|--------|-----|-----|-----|-------|
| /health | GET | 3ms | 8ms | 15ms | Health check |
| /api/projects | GET | 12ms | 45ms | 90ms | List projects |
| /api/projects/{id}/agents | GET | 25ms | 85ms | 150ms | Agent status |
| /api/projects/{id}/feeds/events | GET | 35ms | 120ms | 250ms | Event feed |
| /api/projects/{id}/disruptions | GET | 40ms | 150ms | 300ms | Disruptions |
| /api/analytics/summary | GET | 50ms | 180ms | 350ms | Analytics data |
| /metrics | GET | 8ms | 25ms | 50ms | Prometheus metrics |

### Agent Performance

| Metric | Target | Actual | Notes |
|--------|--------|--------|-------|
| Perceive cycle | < 500ms | 180ms | Feed aggregation |
| Reason cycle (LLM) | < 8s | 3.2s | Claude API call |
| Act cycle | < 500ms | 120ms | Action execution |
| Total cycle | < 10s | 3.5s | Full perceive-reason-act |

### Memory Usage

| Component | Idle | Under Load | Limit |
|-----------|------|------------|-------|
| Backend | 150MB | 400MB | 1GB |
| Frontend (Nginx) | 15MB | 50MB | 256MB |
| PostgreSQL | 200MB | 500MB | 2GB |
| Redis | 30MB | 100MB | 512MB |

### Database Performance

| Query | p50 | p95 | Notes |
|-------|-----|-----|-------|
| SELECT projects | 5ms | 15ms | Simple query |
| INSERT disruption | 10ms | 30ms | With index |
| SELECT feeds (paginated) | 20ms | 80ms | With TimescaleDB compression |
| Agent memory lookup | 30ms | 100ms | Zep Cloud API |

## Optimization Recommendations

### Achieved Optimizations

1. **Connection Pooling**: Redis and PostgreSQL connections are pooled for efficiency
2. **Async Processing**: All I/O operations are async using FastAPI
3. **Pagination**: List endpoints use cursor-based pagination
4. **Compression**: TimescaleDB compression for historical data
5. **Rate Limiting**: slowapi prevents abuse of expensive endpoints
6. **Caching**: Frequently accessed data cached in Redis

### Future Improvements

1. **Query Optimization**: Add composite indexes for common queries
2. **Horizontal Scaling**: Add Redis pub/sub for multi-instance coordination
3. **CDN**: Serve static assets via CDN for global users
4. **Read Replicas**: Offload read queries to replica databases

## Monitoring

### Prometheus Metrics

Access metrics at `/metrics` endpoint. Key metrics:

- `logiswarm_agents_active`: Number of active agents
- `logiswarm_events_total`: Total events processed
- `logiswarm_llm_requests_total`: LLM API requests
- `logiswarm_llm_latency_seconds`: LLM response time
- `http_request_duration_seconds`: API request timing

### Grafana Dashboard

Import the dashboard from `dashboards/logiswarm.json` for visualization.

## Continuous Benchmarking

Add to CI/CD pipeline:

```yaml
# .github/workflows/performance.yml
- name: Run Load Tests
  run: |
    locust -f locustfile.py --host ${{ secrets.TEST_HOST }} \
      --users 50 --spawn-rate 10 -t 2m --headless \
      --html reports/performance.html
```

## Version History

| Version | Date | Notes |
|---------|------|-------|
| v0.2.0 | 2025-03-28 | Initial benchmark documentation |