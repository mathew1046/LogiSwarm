<script setup>
import { ref, computed } from 'vue'
import {
  formatCurrency,
  formatPercentage,
  formatDuration,
  formatWeight,
  formatVolume,
  formatSpeed
} from '@/utils/metrics.js'

const props = defineProps({
  agent: {
    type: Object,
    required: true
  }
})

const activeTab = ref('overview')

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'port-ops', label: 'Port Ops' },
  { id: 'vessels', label: 'Vessels' },
  { id: 'economics', label: 'Economics' },
  { id: 'weather', label: 'Weather' },
  { id: 'risk', label: 'Risk' },
  { id: 'inventory', label: 'Inventory' },
  { id: 'financial', label: 'Financial' },
  { id: 'sustainability', label: 'Sustainability' }
]

// Map topology endpoint field names to component expected names
const mappedAgent = computed(() => {
  const a = props.agent
  return {
    ...a,
    port_ops: a.port_ops || a.port_metrics || {},
    vessels: a.vessels || a.vessel_metrics || {},
    economics: a.economics || a.freight_economics || {},
    weather: a.weather || a.weather_impact || {},
    risk: a.risk || a.risk_signals || {},
    inventory: a.inventory || a.inventory_status || {},
    sustainability: a.sustainability || a.sustainability_metrics || {},
    financial_impact: a.financial_impact || {}
  }
})

function getSeverityClass(severity) {
  return `badge--${(severity || 'low').toLowerCase()}`
}

function getRiskBorderClass(severity) {
  return `risk-${(severity || 'low').toLowerCase()}`
}

function formatTime(dateStr) {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return date.toLocaleDateString()
}

function getConfidencePercent(confidence) {
  return ((confidence || 0) * 100).toFixed(1)
}

// Overview computed
const overviewData = computed(() => {
  const a = mappedAgent.value
  return {
    regionName: a.region_name || a.region_id || 'Unknown Region',
    tier: a.tier || 1,
    specialization: a.specialization || 'General',
    status: a.running ? 'Running' : 'Stopped',
    severity: a.last_assessment?.severity || 'low',
    confidence: getConfidencePercent(a.last_assessment?.confidence),
    lastCycle: formatTime(a.last_cycle_at),
    keyLocations: a.key_locations || [],
    neighbors: a.neighbors || []
  }
})

// Port Ops metrics
const portOpsMetrics = computed(() => {
  const a = mappedAgent.value.port_ops || {}
  return [
    { label: 'Vessel Throughput', value: formatVolume(a.vessel_throughput) },
    { label: 'Avg Dock Time', value: formatDuration(a.avg_dock_time_hours) },
    { label: 'Port Congestion', value: formatPercentage(a.port_congestion_pct) },
    { label: 'Terminal Efficiency', value: formatPercentage(a.terminal_efficiency_pct) }
  ]
})

// Vessels metrics
const vesselMetrics = computed(() => {
  const a = mappedAgent.value.vessels || {}
  return [
    { label: 'Active Vessels', value: a.active_vessels ?? '—' },
    { label: 'Avg Speed', value: formatSpeed(a.avg_speed_knots) },
    { label: 'Total TEU Capacity', value: formatVolume(a.total_teu_capacity) },
    { label: 'Bunkered Vessels', value: a.bunkered_vessels ?? '—' }
  ]
})

// Economics metrics
const economicsMetrics = computed(() => {
  const a = mappedAgent.value.economics || {}
  return [
    { label: 'Daily Operating Cost', value: formatCurrency(a.daily_operating_cost_usd) },
    { label: 'Revenue Per Day', value: formatCurrency(a.revenue_per_day_usd) },
    { label: 'Fuel Cost Index', value: formatCurrency(a.fuel_cost_per_ton) },
    { label: 'Route Cost Delta', value: formatCurrency(a.route_cost_delta_usd) }
  ]
})

// Weather metrics
const weatherMetrics = computed(() => {
  const a = mappedAgent.value.weather || {}
  return [
    { label: 'Wind Speed', value: formatSpeed(a.wind_speed_knots) },
    { label: 'Sea State', value: a.sea_state || '—' },
    { label: 'Visibility', value: a.visibility_nm ? `${a.visibility_nm} nm` : '—' },
    { label: 'Storm Distance', value: formatDistance(a.storm_distance_km) }
  ]
})

// Risk metrics
const riskMetrics = computed(() => {
  const a = mappedAgent.value.risk || {}
  return [
    { label: 'Cascade Risk Score', value: formatPercentage(a.cascade_risk_score * 100) },
    { label: 'Geopolitical Index', value: a.geopolitical_index?.toFixed(2) ?? '—' },
    { label: 'Delay Probability', value: formatPercentage(a.delay_probability_pct) },
    { label: 'Insurance Premium', value: formatCurrency(a.insurance_premium_usd) }
  ]
})

// Inventory metrics
const inventoryMetrics = computed(() => {
  const a = mappedAgent.value.inventory || {}
  return [
    { label: 'Containers In Port', value: formatVolume(a.containers_in_port) },
    { label: 'Avg Dwell Time', value: formatDuration(a.avg_dwell_time_hours) },
    { label: 'Reefer Slots Used', value: a.reefer_slots_used ?? '—' },
    { label: 'Total Weight', value: formatWeight(a.total_weight_kg) }
  ]
})

// Financial metrics
const financialMetrics = computed(() => {
  const a = mappedAgent.value.financial_impact || {}
  return [
    { label: 'Total Revenue Loss', value: formatCurrency(a.total_revenue_loss_usd) },
    { label: 'Cost Overrun', value: formatCurrency(a.cost_overrun_usd) },
    { label: 'Insurance Claims', value: formatCurrency(a.insurance_claims_usd) },
    { label: 'Market Impact', value: formatCurrency(a.market_impact_usd) }
  ]
})

// Sustainability metrics
const sustainabilityMetrics = computed(() => {
  const a = mappedAgent.value.sustainability || {}
  return [
    { label: 'CO2 Emissions', value: formatWeight(a.co2_emissions_kg) },
    { label: 'Fuel Efficiency', value: formatSpeed(a.fuel_efficiency_kn) },
    { label: 'Carbon Intensity', value: formatPercentage(a.carbon_intensity_pct) },
    { label: 'Renewable Share', value: formatPercentage(a.renewable_share_pct) }
  ]
})

function formatDistance(km) {
  if (km == null || isNaN(km) || km < 0) return '—'
  return `${km.toLocaleString()} km`
}
</script>

<template>
  <div :class="['agent-detail-card', 'card', 'card--glass', getRiskBorderClass(overviewData.severity)]">
    <!-- Header -->
    <div class="detail-header">
      <div class="detail-title">
        <h2>{{ overviewData.regionName }}</h2>
        <span :class="['badge', `tier-badge--${overviewData.tier}`]">
          T{{ overviewData.tier }}
        </span>
        <span :class="['badge', getSeverityClass(overviewData.severity)]">
          {{ overviewData.severity.toUpperCase() }}
        </span>
      </div>
      <div class="detail-status">
        <span :class="['status-dot', { 'status-dot--active': overviewData.status === 'Running' }]"></span>
        <span class="status-label">{{ overviewData.status }}</span>
      </div>
    </div>

    <!-- Tabs -->
    <div class="detail-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab-btn', { 'tab-btn--active': activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <div class="detail-content">
      <!-- Overview -->
      <div v-if="activeTab === 'overview'" class="tab-panel fade-in">
        <div class="overview-grid">
          <div class="overview-item">
            <span class="overview-label">Specialization</span>
            <span class="overview-value">{{ overviewData.specialization }}</span>
          </div>
          <div class="overview-item">
            <span class="overview-label">Confidence</span>
            <span class="overview-value text-mono">{{ overviewData.confidence }}%</span>
          </div>
          <div class="overview-item">
            <span class="overview-label">Last Cycle</span>
            <span class="overview-value text-mono">{{ overviewData.lastCycle }}</span>
          </div>
          <div class="overview-item">
            <span class="overview-label">Severity</span>
            <span :class="['badge', getSeverityClass(overviewData.severity)]">
              {{ overviewData.severity.toUpperCase() }}
            </span>
          </div>
        </div>

        <div v-if="overviewData.keyLocations.length" class="info-section">
          <h4 class="info-title">Key Locations</h4>
          <div class="location-tags">
            <span
              v-for="loc in overviewData.keyLocations"
              :key="loc"
              class="location-tag"
            >
              {{ loc }}
            </span>
          </div>
        </div>

        <div v-if="overviewData.neighbors.length" class="info-section">
          <h4 class="info-title">Neighbor Regions</h4>
          <div class="location-tags">
            <span
              v-for="neighbor in overviewData.neighbors"
              :key="neighbor"
              class="location-tag location-tag--neighbor"
            >
              {{ neighbor }}
            </span>
          </div>
        </div>

        <div v-if="!overviewData.keyLocations.length && !overviewData.neighbors.length" class="empty-info">
          <p>No location data available.</p>
        </div>
      </div>

      <!-- Port Ops -->
      <div v-if="activeTab === 'port-ops'" class="tab-panel fade-in">
        <div class="metrics-grid">
          <div v-for="metric in portOpsMetrics" :key="metric.label" class="metric-item">
            <span class="metric-label">{{ metric.label }}</span>
            <span class="metric-value text-mono">{{ metric.value }}</span>
          </div>
        </div>
      </div>

      <!-- Vessels -->
      <div v-if="activeTab === 'vessels'" class="tab-panel fade-in">
        <div class="metrics-grid">
          <div v-for="metric in vesselMetrics" :key="metric.label" class="metric-item">
            <span class="metric-label">{{ metric.label }}</span>
            <span class="metric-value text-mono">{{ metric.value }}</span>
          </div>
        </div>
      </div>

      <!-- Economics -->
      <div v-if="activeTab === 'economics'" class="tab-panel fade-in">
        <div class="metrics-grid">
          <div v-for="metric in economicsMetrics" :key="metric.label" class="metric-item">
            <span class="metric-label">{{ metric.label }}</span>
            <span class="metric-value text-mono">{{ metric.value }}</span>
          </div>
        </div>
      </div>

      <!-- Weather -->
      <div v-if="activeTab === 'weather'" class="tab-panel fade-in">
        <div class="metrics-grid">
          <div v-for="metric in weatherMetrics" :key="metric.label" class="metric-item">
            <span class="metric-label">{{ metric.label }}</span>
            <span class="metric-value text-mono">{{ metric.value }}</span>
          </div>
        </div>
      </div>

      <!-- Risk -->
      <div v-if="activeTab === 'risk'" class="tab-panel fade-in">
        <div class="metrics-grid">
          <div v-for="metric in riskMetrics" :key="metric.label" class="metric-item">
            <span class="metric-label">{{ metric.label }}</span>
            <span class="metric-value text-mono">{{ metric.value }}</span>
          </div>
        </div>
      </div>

      <!-- Inventory -->
      <div v-if="activeTab === 'inventory'" class="tab-panel fade-in">
        <div class="metrics-grid">
          <div v-for="metric in inventoryMetrics" :key="metric.label" class="metric-item">
            <span class="metric-label">{{ metric.label }}</span>
            <span class="metric-value text-mono">{{ metric.value }}</span>
          </div>
        </div>
      </div>

      <!-- Financial -->
      <div v-if="activeTab === 'financial'" class="tab-panel fade-in">
        <div class="metrics-grid">
          <div v-for="metric in financialMetrics" :key="metric.label" class="metric-item">
            <span class="metric-label">{{ metric.label }}</span>
            <span class="metric-value text-mono">{{ metric.value }}</span>
          </div>
        </div>
      </div>

      <!-- Sustainability -->
      <div v-if="activeTab === 'sustainability'" class="tab-panel fade-in">
        <div class="metrics-grid">
          <div v-for="metric in sustainabilityMetrics" :key="metric.label" class="metric-item">
            <span class="metric-label">{{ metric.label }}</span>
            <span class="metric-value text-mono">{{ metric.value }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-detail-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.detail-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.detail-title h2 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
}

.tier-badge--1 {
  background: rgba(59, 130, 246, 0.15);
  color: var(--color-primary-light);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.tier-badge--2 {
  background: rgba(99, 102, 241, 0.15);
  color: var(--color-secondary);
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.tier-badge--3 {
  background: rgba(6, 182, 212, 0.15);
  color: var(--color-info);
  border: 1px solid rgba(6, 182, 212, 0.3);
}

.detail-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.status-label {
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.detail-tabs {
  display: flex;
  gap: var(--spacing-1);
  padding: var(--spacing-2) var(--spacing-4);
  background: var(--color-bg-tertiary);
  overflow-x: auto;
  border-bottom: 1px solid var(--color-border);
}

.tab-btn {
  padding: var(--spacing-2) var(--spacing-3);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.tab-btn:hover {
  color: var(--color-text);
  background: var(--color-surface);
}

.tab-btn--active {
  color: var(--color-text-inverse);
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-4) var(--spacing-5);
}

.tab-panel {
  animation: fadeIn 200ms ease forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Overview Styles */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-4);
}

.overview-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.overview-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.overview-value {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text);
}

.text-mono {
  font-family: var(--font-mono);
}

.info-section {
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border);
}

.info-title {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
  margin: 0 0 var(--spacing-2);
}

.location-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.location-tag {
  font-size: var(--text-xs);
  padding: var(--spacing-1) var(--spacing-2);
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text-secondary);
}

.location-tag--neighbor {
  border-color: var(--color-primary);
  color: var(--color-primary-light);
  background: rgba(59, 130, 246, 0.1);
}

.empty-info {
  text-align: center;
  padding: var(--spacing-6);
}

.empty-info p {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  font-style: italic;
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-4);
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  padding: var(--spacing-3);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.metric-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.metric-value {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
}

/* Responsive */
@media (max-width: 640px) {
  .detail-header {
    flex-direction: column;
    gap: var(--spacing-2);
  }

  .overview-grid,
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .detail-tabs {
    gap: var(--spacing-1);
  }

  .tab-btn {
    padding: var(--spacing-1) var(--spacing-2);
    font-size: 10px;
  }
}
</style>
