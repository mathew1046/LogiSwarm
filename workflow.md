# LogiSwarm Complete Workflow & User Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Interface Guide](#interface-guide)
4. [How to Use Each Feature](#how-to-use-each-feature)
5. [Mock Data & Simulation](#mock-data--simulation)
6. [Troubleshooting](#troubleshooting)

---

## Project Overview

**LogiSwarm** is a geo-aware swarm intelligence platform for supply chain disruption monitoring. It uses AI agents to continuously monitor global shipping routes, detect disruptions before they cascade, and recommend or execute reroutes automatically.

### Key Features
- **8 Regional AI Agents**: Each geographic region has a dedicated AI agent
- **Real-time Monitoring**: AIS vessel tracking, weather data, port sensors
- **LLM-Powered Reasoning**: AI analyzes disruptions and generates recommendations
- **Cascade Prediction**: Multi-hop risk scoring predicts downstream impacts
- **Auto-Routing**: Automatically suggests or executes alternative routes

---

## System Architecture

### Data Flow
```
Data Sources → Geo-Agents → Swarm Orchestrator → Route Optimizer → Action Layer
     ↓              ↓               ↓                    ↓              ↓
   Feeds      Perceive/Reason  Cascade Risk      Recommendations   Alerts/Reports
```

### Core Components

#### 1. **Geo-Agents** (8 Regional Agents)
Each agent monitors a specific region:
- **Gulf/Suez** (`gulf_suez`): Monitors Suez Canal, Red Sea, Persian Gulf
- **Southeast Asia** (`se_asia`): Strait of Malacca, Singapore, Port Klang
- **Europe** (`europe`): Rotterdam, Hamburg, Antwerp corridor
- **North America** (`north_america`): LA/Long Beach, Chicago rail hub
- **China/East Asia** (`china_ea`): Shanghai, Ningbo, Busan manufacturing export
- **South Asia** (`south_asia`): Indian Ocean, Colombo, Mumbai
- **Latin America** (`latin_america`): Panama Canal, Brazilian ports
- **Africa** (`africa`): Cape of Good Hope, Durban, Cape Town

**Agent Lifecycle:**
1. **Perceive**: Collect data from feeds every 60 seconds
2. **Reason**: LLM analyzes data and generates risk assessment
3. **Act**: Broadcast alerts, trigger recommendations, update memory

#### 2. **Feed Aggregator**
Collects data from multiple sources:
- **AIS Vessel Positions**: Real-time ship tracking
- **Weather APIs**: Storms, hurricanes, severe weather
- **Port Sensors**: Crane utilization, queue depth, dwell times
- **Geopolitical News**: Political instability, strikes, conflicts
- **Carrier APIs**: Shipping delays, booking data

#### 3. **Swarm Orchestrator**
Coordinates between agents:
- **Cascade Risk Scoring**: Calculates how disruptions spread to neighbors
- **Propagation Model**: Multi-hop impact analysis
- **Neighbor Communication**: Agents alert each other via Redis pub/sub

#### 4. **Route Optimizer**
Calculates alternative shipping routes:
- **Multi-modal Graph**: Sea, air, rail connections
- **Disruption-aware**: Avoids blocked regions
- **Cost vs. Delay Trade-offs**: Optimizes for speed or cost

#### 5. **Action Layer**
Executes decisions:
- **Alerts**: Slack, Email notifications
- **Auto-Reroute**: Automatic TMS updates (if enabled)
- **Reports**: Generate PDF reports with full audit trail

---

## Interface Guide

### Navigation Tabs

#### 1. **Dashboard (Home)**
**URL**: `/`

The main control center showing:
- **World Risk Map**: Color-coded heat map of all regions
- **Active Disruptions**: List of current disruptions with severity
- **Agent Status**: Health check for all 8 regional agents
- **Recent Activity**: Latest events and decisions

**How to use:**
- Monitor overall system health
- Quickly identify high-risk regions (red on map)
- Click any region to view detailed status

---

#### 2. **Projects**
**URL**: `/projects`

Manage supply chain monitoring projects:
- **Create Project**: Define which regions to monitor
- **Project Details**: View shipments, routes, disruptions per project
- **Multi-tenancy**: Isolate different supply chains

**How to use:**
1. Click "New Project"
2. Select regions relevant to your supply chain
3. Add shipments to track
4. View project-specific analytics

---

#### 3. **World Map**
**URL**: `/map`

Interactive geographic visualization:
- **Vessel Positions**: Real-time AIS tracking
- **Risk Heat Map**: Color-coded by disruption probability
- **Route Visualization**: Current and alternative routes
- **Port Status**: Click ports for congestion data

**How to use:**
- Pan/zoom to explore different regions
- Click vessels for ship details
- Toggle layers (risk, vessels, routes)
- Hover over regions for quick stats

---

#### 4. **Agents**
**URL**: `/agents`

Detailed view of all 8 regional agents:
- **Agent Cards**: Status, last cycle time, current assessment
- **Degradation Status**: Whether feeds are operating normally
- **Memory**: Historical episodes and learnings
- **Configuration**: Tune sensitivity, thresholds per agent

**How to use:**
- View per-agent risk assessments
- Configure agent settings (sensitivity, LLM model)
- Force manual assessment
- Interview agent about its region

---

#### 5. **Disruptions**
**URL**: `/disruptions`

Central hub for disruption management:
- **Active Disruptions**: Current events with severity
- **Disruption Feed**: Real-time stream of new events
- **Filter & Search**: By region, type, severity, date
- **Resolution Tracking**: Monitor as disruptions resolve

**How to use:**
- Monitor new disruptions as they appear
- Click any disruption for detailed analysis
- View affected routes and recommendations
- Mark disruptions as resolved

---

#### 6. **Shipments**
**URL**: `/shipments`

Track individual shipments through the supply chain:
- **Shipment List**: All tracked shipments with status
- **ETA Tracking**: Predicted vs. actual arrival times
- **Risk Assessment**: Per-shipment risk scores
- **Bulk Import**: Upload CSV of shipments

**How to use:**
1. Add shipments manually or via CSV upload
2. Monitor ETA changes as disruptions occur
3. Receive automatic reroute recommendations
4. Track shipment journey on map

---

#### 7. **Routes**
**URL**: `/routes`

Route planning and optimization:
- **Route Library**: Saved common routes
- **Route Optimizer**: Calculate alternatives
- **Multi-modal Options**: Sea, air, rail combinations
- **Cost Analysis**: Compare route costs and times

**How to use:**
1. Enter origin and destination
2. View optimized route options
3. Compare cost vs. time trade-offs
4. Save preferred routes

---

#### 8. **Reports**
**URL**: `/reports`

Generate and view analysis reports:
- **Post-Disruption Reports**: Automated incident analysis
- **Custom Reports**: Query-specific analysis
- **Chat Interface**: Ask questions about reports
- **Export Options**: PDF, JSON formats

**How to use:**
- Generate reports after major disruptions
- Use chat to query report data
- Export for stakeholder sharing
- Compare historical reports

---

#### 9. **Analytics**
**URL**: `/analytics`

Data visualization and insights:
- **Severity Distribution**: Breakdown of disruption types
- **Timeline Charts**: Disruption history over time
- **Regional Metrics**: Performance by region
- **Accuracy Tracking**: Prediction accuracy over time

**How to use:**
- Analyze trends in your supply chain
- Identify problematic routes or regions
- Track system accuracy improvements
- Export charts for presentations

---

#### 10. **Simulation** ⭐ NEW
**URL**: `/simulation`

Test scenarios without affecting production data:
- **Scenario Builder**: Create custom disruption scenarios
- **What-if Analysis**: See how hypothetical events cascade
- **Mock Data Generator**: Inject realistic test data
- **Simulation Reports**: Analyze simulated outcomes

**How to use:** (See detailed section below)

---

## How to Use Each Feature

### Creating Your First Project

1. **Navigate to Projects** → Click "New Project"
2. **Enter Details**:
   - Name: "Asia-Europe Trade Lane"
   - Description: Monitor routes from Shanghai to Rotterdam
3. **Select Regions**:
   - Check: China/East Asia, Southeast Asia, Europe
4. **Add Shipments**:
   - Upload CSV or add manually
   - Example: SHANGHAI → ROTTERDAM, Container Ship XYZ
5. **Activate**: Click "Start Monitoring"

### Monitoring Real-Time Events

1. **Dashboard View**:
   - Watch the world map for color changes
   - Red = Critical disruption, Yellow = Warning, Green = Normal
   
2. **Disruption Feed**:
   - New events appear in real-time
   - Shows: Region, Type, Severity, Timestamp
   
3. **Agent Status**:
   - Green dot = Agent running normally
   - Yellow dot = Degraded (using cached data)
   - Red dot = Agent offline

### Responding to Disruptions

When a disruption is detected:

1. **View Alert**: Click notification or disruption in feed
2. **Read Assessment**: AI-generated severity and impact analysis
3. **Check Recommendations**: Alternative routes if available
4. **Take Action**:
   - **Manual**: Review and approve recommendation
   - **Auto**: System automatically reroutes (if enabled)
5. **Track Resolution**: Monitor as disruption clears

### Interviewing Agents

Ask an agent about its region:

1. Go to **Agents** tab
2. Click on any agent card (e.g., "Gulf/Suez")
3. Scroll to "Interview Agent" section
4. Ask questions like:
   - "What's the current status of the Suez Canal?"
   - "What weather risks are you tracking?"
   - "How has port congestion changed this week?"
5. The agent responds based on its memory and current data

### Generating Reports

1. Go to **Reports** tab
2. Click "Generate Report"
3. Select:
   - Report type: Post-disruption / Custom
   - Language: English / Chinese
   - Date range
4. Wait for AI to generate (30-60 seconds)
5. View report with:
   - Executive summary
   - Timeline of events
   - Agent assessments
   - Recommendations
   - Full audit trail

---

## Mock Data & Simulation

### Overview

The **Simulation** tab allows you to test scenarios without affecting real operations. Perfect for:
- Training new users
- Testing system responses
- Validating configuration changes
- Demonstrating capabilities to stakeholders

### Types of Simulation

#### 1. **Port Sensor Simulation**
Generates realistic port telemetry data with occasional anomalies.

**Configuration** (in `.env`):
```bash
PORT_MOCK_ENABLED=true          # Enable mock port data
PORT_MOCK_ANOMALY_PROB=0.12     # 12% chance of anomaly per reading
```

**What it simulates:**
- Crane utilization (55-88% normal, spikes to 95%+ during anomalies)
- Vessel queue depth (4-18 ships normal, 25+ during congestion)
- Gate throughput (85-240 containers/hour)
- Dwell time (8-28 hours normal, 48+ during disruptions)

**Anomaly types:**
- `CONGESTION`: Port overwhelmed
- `EQUIPMENT_FAILURE`: Crane breakdown
- `WEATHER_DELAY`: Storm impact
- `LABOR_STRIKE`: Worker slowdown

#### 2. **Scenario Simulation**

Run complete what-if scenarios:

**Step 1**: Go to **Simulation** tab

**Step 2**: Choose a scenario type:

**Option A: Suez Canal Blockage** (Classic Example)
- Simulates: Mega-container ship stuck in canal
- Duration: 6-7 days
- Impact: Europe-Asia routes diverted around Africa
- Cascade: +14 days transit time, +$300k fuel cost

**Option B: Port Strike**
- Simulates: Labor dispute shuts down major port
- Duration: 2-14 days
- Impact: Vessels reroute to alternative ports
- Cascade: Inventory shortages, production delays

**Option C: Hurricane Season**
- Simulates: Category 4 hurricane hits Gulf Coast
- Duration: 3-5 days
- Impact: Port closures, vessel diversions
- Cascade: Chemical/oil supply disruptions

**Option D: Custom Scenario**
- Define your own:
  - Region affected
  - Event type
  - Severity level
  - Duration
  - Cascading impacts

**Step 3**: Run Simulation
- Click "Start Simulation"
- Watch real-time agent responses
- See cascade predictions
- View alternative routes
- Generate simulation report

#### 3. **Bulk Data Injection**

Inject historical data for testing:

```bash
# Via API
curl -X POST http://localhost:5001/shipments/bulk \
  -H "Content-Type: application/json" \
  -d @mock_shipments.json
```

**Mock data includes:**
- 100+ sample shipments
- Various carriers (Maersk, MSC, CMA-CGM)
- Multiple routes (Asia-Europe, Trans-Pacific)
- Realistic vessel names and ETAs

### Running a Simulation Walkthrough

**Example: Simulate Suez Canal Blockage**

1. **Navigate**: Simulation tab
2. **Select Scenario**: "Suez Canal Blockage"
3. **Configure**:
   - Start Date: Today
   - Duration: 6 days
   - Severity: CRITICAL
4. **Click**: "Inject Simulation"
5. **Watch Dashboard**:
   - Gulf/Suez agent turns RED
   - Neighboring agents (Europe, SE Asia) turn YELLOW
   - Risk map updates
6. **View Disruptions**: New "Canal Blockage" event appears
7. **Check Recommendations**: Route optimizer suggests Africa route
8. **Interview Agent**: Ask Gulf/Suez agent about impact
9. **Generate Report**: Create post-incident analysis
10. **Reset**: Click "Clear Simulation" to return to normal

### Simulation Best Practices

1. **Always use simulation mode** for training
2. **Start small**: Test single-region scenarios first
3. **Monitor cascade**: Watch how disruptions spread
4. **Test auto-actions**: Enable auto-reroute to see automation
5. **Document results**: Save simulation reports
6. **Reset after testing**: Clear simulation to avoid confusion

---

## Troubleshooting

### Common Issues

#### 1. **502 Proxy Error**
**Symptom**: Frontend shows "Proxy Error"
**Solution**: 
```bash
docker compose restart backend
```

#### 2. **Agent Shows "Degraded"**
**Symptom**: Agent status = YELLOW
**Cause**: Feed connectors not responding
**Solution**: Check external APIs (weather, AIS) or enable mock data

#### 3. **No Disruptions Appearing**
**Symptom**: Dashboard empty
**Solution**: 
- Enable PORT_MOCK_ENABLED=true
- Run simulation scenario
- Wait 60-120 seconds for first agent cycle

#### 4. **LLM Rate Limiting**
**Symptom**: Agents show "fallback assessment"
**Solution**: Check LLM API key and rate limits

#### 5. **CORS Errors**
**Symptom**: Browser blocks API requests
**Solution**: Verify CORS_ALLOW_ORIGINS includes frontend URL

### Getting Help

- Check logs: `docker compose logs -f backend`
- API docs: http://localhost:5001/docs
- Health check: http://localhost:5001/health

---

## Quick Reference

### API Endpoints

**Health & Status**
- `GET /health` - System health
- `GET /agents` - All agent statuses
- `GET /agents/{region}/status` - Specific agent

**Data**
- `GET /disruptions` - Active disruptions
- `GET /shipments` - Tracked shipments
- `GET /routes` - Saved routes

**Actions**
- `POST /disruptions` - Create disruption
- `POST /shipments` - Add shipment
- `POST /orchestrator/simulate` - Run simulation

**Reports**
- `POST /reports` - Generate report
- `GET /reports/{id}` - View report

### Environment Variables

**Required**
- `LLM_API_KEY` - OpenAI/Anthropic API key
- `DATABASE_URL` - PostgreSQL connection
- `JWT_SECRET_KEY` - Authentication secret

**Optional**
- `PORT_MOCK_ENABLED=true` - Enable mock data
- `ZEP_API_KEY` - Memory service (optional)
- `CORS_ALLOW_ORIGINS` - Frontend URLs

---

## Summary

LogiSwarm provides a complete supply chain intelligence platform:

1. **Monitor**: 8 regional agents watch global routes
2. **Detect**: AI identifies disruptions in real-time
3. **Predict**: Cascade modeling shows downstream impacts
4. **Recommend**: Route optimizer suggests alternatives
5. **Act**: Automatic or manual response execution
6. **Learn**: Episodic memory improves future responses

Use the **Simulation** tab to explore capabilities risk-free!
