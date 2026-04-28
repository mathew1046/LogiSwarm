<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { useThemeStore } from '@/stores/theme'
import { formatPercentage } from '@/utils/metrics.js'

const mapContainer = ref(null)
const selectedRegion = ref(null)
const map = ref(null)
const layers = ref([])
const baseLayer = ref(null)

const agentStore = useAgentStore()
const themeStore = useThemeStore()
const isDark = computed(() => themeStore.isDark())

const searchQuery = ref('')
const tierFilter = ref('all')
const topologyData = ref({})
const agentsWithBbox = ref([])

const filteredAgents = computed(() => {
  let filtered = agentsWithBbox.value
  if (tierFilter.value !== 'all') {
    filtered = filtered.filter(a => {
      const tier = a.tier || 1
      return tier.toString() === tierFilter.value
    })
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    filtered = filtered.filter(a =>
      a.region_id?.toLowerCase().includes(q) ||
      a.region_name?.toLowerCase().includes(q)
    )
  }
  return filtered
})

function getSeverityColor(severity) {
  if (!severity) return '#475569'
  const colors = {
    low: '#22c55e',
    medium: '#eab308',
    high: '#f97316',
    critical: '#ef4444'
  }
  return colors[severity.toLowerCase()] || '#475569'
}

function getConfidenceOpacity(confidence, base = 0.15, max = 0.45) {
  const c = confidence || 0.5
  return base + (max - base) * c
}

function getTierWeight(tier) {
  const t = tier || 1
  if (t === 1) return 3
  if (t === 2) return 2
  return 1
}

function getSeverityClass(severity) {
  return `badge--${(severity || 'low').toLowerCase()}`
}

function getConfidencePercent(confidence) {
  return ((confidence || 0) * 100).toFixed(1)
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

function getTierBadgeClass(tier) {
  return `tier-badge--${tier || 1}`
}

function darkenColor(hex, factor = 20) {
  const num = parseInt(hex.slice(1), 16)
  const amt = Math.round(2.55 * factor)
  const R = Math.max(0, (num >> 16) - amt)
  const G = Math.max(0, ((num >> 8) & 0x00FF) - amt)
  const B = Math.max(0, (num & 0x0000FF) - amt)
  return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1)
}

async function fetchTopology() {
  try {
    const response = await fetch('/api/agents/topology')
    const data = await response.json()
    if (data.error) return
    topologyData.value = data.data || {}
  } catch (e) {
    console.error('Failed to fetch topology:', e)
  }
}

function mergeAgentData() {
  const nodes = topologyData.value.nodes || []
  const nodeMap = {}
  nodes.forEach(n => { nodeMap[n.region_id] = n })

  agentsWithBbox.value = agentStore.agents.map(agent => {
    const node = nodeMap[agent.region_id]
    const rawBbox = node?.bbox
    // Convert flat [west, south, east, north] to Leaflet [[south, west], [north, east]]
    let leafletBbox = null
    if (rawBbox && rawBbox.length === 4) {
      leafletBbox = [[rawBbox[1], rawBbox[0]], [rawBbox[3], rawBbox[2]]]
    }
    return {
      ...agent,
      bbox: leafletBbox,
      center_lat: node?.center_lat || null,
      center_lon: node?.center_lon || null
    }
  }).filter(a => a.bbox)
}

function initMap() {
  if (!mapContainer.value || typeof window === 'undefined') return

  const L = window.L
  if (!L) return

  map.value = L.map(mapContainer.value, {
    center: [20, 0],
    zoom: 2,
    minZoom: 1,
    maxZoom: 10
  })

  updateBaseLayer()
  updateOverlays()
}

function updateBaseLayer() {
  if (!map.value || typeof window === 'undefined') return

  const L = window.L
  if (!L) return

  if (baseLayer.value) {
    map.value.removeLayer(baseLayer.value)
  }

  if (isDark.value) {
    baseLayer.value = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19,
      noWrap: true
    })
  } else {
    baseLayer.value = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      noWrap: true
    })
  }

  baseLayer.value.addTo(map.value)
}

function clearOverlays() {
  layers.value.forEach(layer => layer.remove())
  layers.value = []
}

function updateOverlays() {
  if (!map.value || typeof window === 'undefined') return

  const L = window.L
  if (!L) return

  clearOverlays()

  filteredAgents.value.forEach(agent => {
    const severity = (agent.last_assessment?.severity || 'low').toLowerCase()
    const confidence = agent.last_assessment?.confidence || 0.5
    const color = getSeverityColor(severity)
    const opacity = getConfidenceOpacity(confidence)
    const weight = getTierWeight(agent.tier)
    const isPulsing = severity === 'critical' || severity === 'high'

    const bounds = L.latLngBounds(agent.bbox)

    let options = {
      color: darkenColor(color, 30),
      weight: weight,
      fillColor: color,
      fillOpacity: opacity,
      smoothFactor: 0.5
    }

    if (isPulsing) {
      options.className = `risk-overlay risk-overlay--${severity}`
    }

    const rectangle = L.rectangle(bounds, options)

    const popupContent = `
      <div class="region-popup">
        <div class="popup-header">
          <h3 class="popup-title">${agent.region_name || agent.region_id}</h3>
          <div class="popup-badges">
            <span class="badge ${getTierBadgeClass(agent.tier)}">T${agent.tier || 1}</span>
            <span class="badge ${getSeverityClass(severity)}">${severity.toUpperCase()}</span>
          </div>
        </div>
        <div class="popup-status">
          <span class="status-dot ${agent.running ? 'status-dot--active' : ''}"></span>
          <span class="status-label">${agent.running ? 'Active' : 'Inactive'}</span>
        </div>
        <div class="popup-grid">
          <div class="popup-item">
            <span class="popup-label">Specialization</span>
            <span class="popup-value">${agent.specialization || 'General'}</span>
          </div>
          <div class="popup-item">
            <span class="popup-label">Confidence</span>
            <span class="popup-value text-mono">${getConfidencePercent(confidence)}%</span>
          </div>
          <div class="popup-item">
            <span class="popup-label">Last Cycle</span>
            <span class="popup-value text-mono">${formatTime(agent.last_cycle_at)}</span>
          </div>
        </div>
        ${(agent.key_locations && agent.key_locations.length) ? `
        <div class="popup-section">
          <span class="popup-section-title">Key Locations</span>
          <div class="popup-tags">
            ${agent.key_locations.map(loc => `<span class="popup-tag">${loc}</span>`).join('')}
          </div>
        </div>
        ` : ''}
        ${(agent.neighbors && agent.neighbors.length) ? `
        <div class="popup-section">
          <span class="popup-section-title">Neighbor Regions</span>
          <div class="popup-tags">
            ${agent.neighbors.map(n => `<span class="popup-tag popup-tag--neighbor">${n}</span>`).join('')}
          </div>
        </div>
        ` : ''}
      </div>
    `

    rectangle.bindPopup(popupContent, { maxWidth: 280, maxHeight: 300 })

    rectangle.on('click', () => {
      selectedRegion.value = agent.region_id
    })

    rectangle.addTo(map.value)
    layers.value.push(rectangle)
  })
}

function flyToAgent(regionId) {
  const agent = agentsWithBbox.value.find(a => a.region_id === regionId)
  if (!agent || !map.value) return

  if (agent.center_lat && agent.center_lon) {
    map.value.flyTo([agent.center_lat, agent.center_lon], 5, { duration: 1 })
  } else if (agent.bbox) {
    const bounds = L.latLngBounds(agent.bbox)
    map.value.flyToBounds(bounds, { padding: [50, 50], duration: 1 })
  }
}

function handleSearch() {
  if (!searchQuery.value.trim()) return
  const q = searchQuery.value.toLowerCase()
  const match = agentsWithBbox.value.find(a =>
    a.region_id?.toLowerCase().includes(q) ||
    a.region_name?.toLowerCase().includes(q)
  )
  if (match) {
    flyToAgent(match.region_id)
    selectedRegion.value = match.region_id
  }
}

watch(tierFilter, () => {
  updateOverlays()
})

watch(searchQuery, () => {
  updateOverlays()
})

watch(() => agentStore.agents, () => {
  mergeAgentData()
  updateOverlays()
}, { deep: true })

watch(() => topologyData.value, () => {
  mergeAgentData()
  updateOverlays()
}, { deep: true })

watch(() => isDark.value, () => {
  updateBaseLayer()
})

onMounted(async () => {
  await agentStore.fetchAgents()
  await fetchTopology()
  mergeAgentData()

  if (typeof window !== 'undefined') {
    const existingScript = document.querySelector('script[src*="leaflet"]')
    if (!existingScript) {
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
      document.head.appendChild(link)

      const script = document.createElement('script')
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
      script.onload = initMap
      document.head.appendChild(script)
    } else {
      initMap()
    }
  }
})

onUnmounted(() => {
  if (map.value) {
    map.value.remove()
    map.value = null
  }
})
</script>

<template>
  <div class="risk-map">
    <div class="map-header glass">
      <div class="header-left">
        <h2>Global Risk Map</h2>
        <div class="tier-filter">
          <button
            :class="['filter-btn', { active: tierFilter === 'all' }]"
            @click="tierFilter = 'all'"
          >All</button>
          <button
            :class="['filter-btn', { active: tierFilter === '1' }]"
            @click="tierFilter = '1'"
          >T1</button>
          <button
            :class="['filter-btn', { active: tierFilter === '2' }]"
            @click="tierFilter = '2'"
          >T2</button>
          <button
            :class="['filter-btn', { active: tierFilter === '3' }]"
            @click="tierFilter = '3'"
          >T3</button>
        </div>
      </div>
      <div class="header-right">
        <div class="map-search">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search agent..."
            class="search-input"
            @keyup.enter="handleSearch"
          />
          <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
          </svg>
        </div>
        <div class="map-legend">
          <span class="legend-item">
            <span class="legend-color legend-color--low"></span>
            <span class="legend-label">Low</span>
          </span>
          <span class="legend-item">
            <span class="legend-color legend-color--medium"></span>
            <span class="legend-label">Medium</span>
          </span>
          <span class="legend-item">
            <span class="legend-color legend-color--high"></span>
            <span class="legend-label">High</span>
          </span>
          <span class="legend-item">
            <span class="legend-color legend-color--critical"></span>
            <span class="legend-label">Critical</span>
          </span>
        </div>
      </div>
    </div>

    <div ref="mapContainer" class="map-container"></div>

    <div v-if="selectedRegion" class="region-detail card card--glass">
      <button class="close-btn" @click="selectedRegion = null">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <template v-if="filteredAgents.find(a => a.region_id === selectedRegion)">
        <h3>{{ filteredAgents.find(a => a.region_id === selectedRegion)?.region_name || selectedRegion }}</h3>
        <div class="detail-stats">
          <div class="stat-row">
            <span class="stat-label">Tier:</span>
            <span class="stat-value">{{ filteredAgents.find(a => a.region_id === selectedRegion)?.tier || 1 }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Specialization:</span>
            <span class="stat-value">{{ filteredAgents.find(a => a.region_id === selectedRegion)?.specialization || 'N/A' }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Severity:</span>
            <span :class="['badge', `badge--${(filteredAgents.find(a => a.region_id === selectedRegion)?.last_assessment?.severity || 'low').toLowerCase()}`]">
              {{ (filteredAgents.find(a => a.region_id === selectedRegion)?.last_assessment?.severity || 'LOW').toUpperCase() }}
            </span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Confidence:</span>
            <span class="stat-value text-mono">{{ ((filteredAgents.find(a => a.region_id === selectedRegion)?.last_assessment?.confidence || 0) * 100).toFixed(1) }}%</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Status:</span>
            <span :class="['status-indicator', filteredAgents.find(a => a.region_id === selectedRegion)?.running ? 'status-active' : 'status-inactive']">
              {{ filteredAgents.find(a => a.region_id === selectedRegion)?.running ? 'Active' : 'Inactive' }}
            </span>
          </div>
        </div>
      </template>
      <template v-else>
        <h3>{{ selectedRegion }}</h3>
        <p class="stat-text">Agent data not available</p>
      </template>
    </div>
  </div>
</template>

<style scoped>
.risk-map {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-color);
  z-index: 10;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.map-header h2 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
}

.tier-filter {
  display: flex;
  gap: var(--spacing-1);
}

.filter-btn {
  padding: var(--spacing-1) var(--spacing-3);
  font-size: var(--text-xs);
  font-weight: 500;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-btn:hover {
  background-color: var(--bg-tertiary);
  color: var(--text);
}

.filter-btn.active {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

.map-search {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  padding: var(--spacing-1) var(--spacing-3);
  padding-left: var(--spacing-8);
  font-size: var(--text-sm);
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text);
  width: 160px;
  transition: all var(--transition-fast);
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px var(--primary-color-glow);
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.search-icon {
  position: absolute;
  left: var(--spacing-2);
  color: var(--text-tertiary);
  pointer-events: none;
}

.map-legend {
  display: flex;
  gap: var(--spacing-3);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.legend-color {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-sm);
}

.legend-color--low {
  background: var(--color-low);
  box-shadow: 0 0 6px var(--color-low-glow);
}

.legend-color--medium {
  background: var(--color-medium);
  box-shadow: 0 0 6px var(--color-medium-glow);
}

.legend-color--high {
  background: var(--color-high);
  box-shadow: 0 0 6px var(--color-high-glow);
}

.legend-color--critical {
  background: var(--color-critical);
  box-shadow: 0 0 6px var(--color-critical-glow);
  animation: criticalPulse 2s infinite;
}

@keyframes criticalPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.legend-label {
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.map-container {
  flex: 1;
  min-height: 400px;
  background-color: var(--bg);
}

.region-detail {
  position: absolute;
  bottom: var(--spacing-4);
  right: var(--spacing-4);
  width: 280px;
  max-height: 320px;
  overflow-y: auto;
  z-index: 1000;
  animation: fadeIn 200ms ease;
}

.close-btn {
  position: absolute;
  top: var(--spacing-2);
  right: var(--spacing-2);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  cursor: pointer;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background-color: var(--bg-secondary);
  color: var(--text);
}

.region-detail h3 {
  margin: 0 0 var(--spacing-3);
  padding-right: var(--spacing-6);
  font-size: var(--text-lg);
  font-weight: 600;
}

.detail-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.stat-value {
  font-weight: 500;
  font-size: var(--text-sm);
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--text-sm);
}

.status-indicator::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-active::before {
  background: var(--color-low);
  box-shadow: 0 0 4px var(--color-low-glow);
}

.status-inactive::before {
  background: var(--text-tertiary);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

:deep(.severity-badge) {
  display: inline-block;
  padding: 2px 6px;
  font-size: var(--text-xs);
  font-weight: 600;
  border-radius: var(--radius-sm);
  text-transform: uppercase;
}

:deep(.severity-badge--low) {
  background: var(--color-low-bg);
  color: var(--color-low);
}

:deep(.severity-badge--medium) {
  background: var(--color-medium-bg);
  color: var(--color-medium);
}

:deep(.severity-badge--high) {
  background: var(--color-high-bg);
  color: var(--color-high);
}

:deep(.severity-badge--critical) {
  background: var(--color-critical-bg);
  color: var(--color-critical);
}

:deep(.region-popup h3) {
  margin: 0 0 var(--spacing-2);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text);
}

:deep(.region-popup p) {
  margin: var(--spacing-1) 0;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

:deep(.region-popup strong) {
  color: var(--text);
}

/* Enhanced Popup Styles */
:deep(.popup-header) {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-2);
  gap: var(--spacing-2);
}

:deep(.popup-title) {
  margin: 0 !important;
  font-size: var(--text-sm) !important;
  font-weight: 600;
  color: var(--color-text) !important;
  flex: 1;
}

:deep(.popup-badges) {
  display: flex;
  gap: var(--spacing-1);
  flex-shrink: 0;
}

:deep(.popup-status) {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  margin-bottom: var(--spacing-3);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

:deep(.popup-grid) {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
}

:deep(.popup-item) {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

:deep(.popup-label) {
  font-size: 10px;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

:deep(.popup-value) {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text);
}

:deep(.popup-section) {
  padding-top: var(--spacing-2);
  border-top: 1px solid var(--color-border);
  margin-top: var(--spacing-2);
}

:deep(.popup-section-title) {
  display: block;
  font-size: 10px;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
  margin-bottom: var(--spacing-1);
}

:deep(.popup-tags) {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-1);
}

:deep(.popup-tag) {
  font-size: 10px;
  padding: 2px 6px;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text-secondary);
}

:deep(.popup-tag--neighbor) {
  border-color: var(--color-primary);
  color: var(--color-primary-light);
  background: rgba(59, 130, 246, 0.1);
}

:deep(.tier-badge--1) {
  background: rgba(59, 130, 246, 0.15);
  color: var(--color-primary-light);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

:deep(.tier-badge--2) {
  background: rgba(99, 102, 241, 0.15);
  color: var(--color-secondary);
  border: 1px solid rgba(99, 102, 241, 0.3);
}

:deep(.tier-badge--3) {
  background: rgba(6, 182, 212, 0.15);
  color: var(--color-info);
  border: 1px solid rgba(6, 182, 212, 0.3);
}
</style>

<style>
.risk-overlay--critical {
  animation: overlayPulseCritical 2s ease-in-out infinite;
}

.risk-overlay--high {
  animation: overlayPulseHigh 3s ease-in-out infinite;
}

@keyframes overlayPulseCritical {
  0%, 100% {
    stroke-opacity: 1;
    filter: drop-shadow(0 0 4px rgba(239, 68, 68, 0.6));
  }
  50% {
    stroke-opacity: 0.5;
    filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.9));
  }
}

@keyframes overlayPulseHigh {
  0%, 100% {
    stroke-opacity: 0.8;
    filter: drop-shadow(0 0 3px rgba(249, 115, 22, 0.5));
  }
  50% {
    stroke-opacity: 0.4;
    filter: drop-shadow(0 0 6px rgba(249, 115, 22, 0.8));
  }
}
</style>
