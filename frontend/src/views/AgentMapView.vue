<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAgentStore } from '@/stores/agent'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'
import AgentDetailCard from '@/components/agents/AgentDetailCard.vue'

const agentStore = useAgentStore()

const mapContainer = ref(null)
const map = ref(null)
const baseLayer = ref(null)
const markersLayer = ref(null)
const edgesLayer = ref(null)

const showIntercomm = ref(false)
const selectedTier = ref('all')
const selectedAgent = ref(null)
const topologyData = ref(null)
const panelLoading = ref(false)
const panelError = ref(null)

const agents = computed(() => agentStore.agents)
const totalAgents = computed(() => agents.value.length)

const SEVERITY_COLORS = {
  LOW: '#22c55e',
  MEDIUM: '#eab308',
  HIGH: '#f97316',
  CRITICAL: '#ef4444'
}

const TIER_RADII = { 1: 10, 2: 7, 3: 4 }
const TIER_LABELS = { all: 'All', 1: 'T1', 2: 'T2', 3: 'T3' }

function getSeverityColor(severity) {
  return SEVERITY_COLORS[(severity || 'LOW').toUpperCase()] || SEVERITY_COLORS.LOW
}

function getTierRadius(tier) {
  return TIER_RADII[tier] || 5
}

function filteredAgents() {
  if (selectedTier.value === 'all') return topologyData.value?.nodes || []
  return (topologyData.value?.nodes || []).filter(n => String(n.tier) === String(selectedTier.value))
}

async function loadTopology() {
  try {
    const res = await fetch('/api/agents/topology')
    if (res.ok) {
      const json = await res.json()
      topologyData.value = json.data
    }
  } catch { /* offline */ }
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

  baseLayer.value = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19,
    noWrap: true
  })
  baseLayer.value.addTo(map.value)

  markersLayer.value = L.layerGroup().addTo(map.value)
  edgesLayer.value = L.layerGroup().addTo(map.value)

  renderMarkers()
}

function renderMarkers() {
  if (!map.value || typeof window === 'undefined') return
  const L = window.L
  if (!L || !topologyData.value) return

  markersLayer.value.clearLayers()
  const nodes = filteredAgents()
  const selId = selectedAgent.value?.region_id

  nodes.forEach(node => {
    const color = getSeverityColor(node.severity)
    const radius = getTierRadius(node.tier)
    const isSelected = node.region_id === selId

    const icon = L.divIcon({
      className: '',
      html: `<div class="agent-marker ${node.running ? 'running' : ''}" style="
        width: ${radius * 2}px;
        height: ${radius * 2}px;
        background: ${color};
        border: ${isSelected ? '2px solid #fff' : '1.5px solid rgba(255,255,255,0.3)'};
        border-radius: 50%;
        box-shadow: 0 0 ${radius}px ${color}80;
        cursor: pointer;
      "></div>`,
      iconSize: [radius * 2, radius * 2],
      iconAnchor: [radius, radius]
    })

    const marker = L.marker([node.center_lat, node.center_lon], { icon })
    marker.on('click', () => selectAgent(node))
    markersLayer.value.addLayer(marker)
  })
}

function renderEdges() {
  if (!map.value || typeof window === 'undefined') return
  const L = window.L
  if (!L || !topologyData.value) return

  edgesLayer.value.clearLayers()
  if (!showIntercomm.value) return

  const selId = selectedAgent.value?.region_id
  const edgeColor = '#ffffff'

  ;(topologyData.value.edges || []).forEach(edge => {
    const isHighlighted = selId && (edge.source === selId || edge.target === selId)
    const opacity = isHighlighted ? 0.6 : 0.15
    const weight = isHighlighted ? 2 : 1

    const poly = L.polyline(
      [[edge.source_lat, edge.source_lon], [edge.target_lat, edge.target_lon]],
      { color: edgeColor, weight, opacity }
    )
    edgesLayer.value.addLayer(poly)
  })
}

function selectAgent(node) {
  selectedAgent.value = node
  renderEdges()
}

function closePanel() {
  selectedAgent.value = null
  renderEdges()
}

function setTier(t) {
  selectedTier.value = t
  renderMarkers()
}

function toggleIntercomm() {
  showIntercomm.value = !showIntercomm.value
  renderEdges()
}

function formatNeighbors(node) {
  return (node.neighbors || []).map(n => typeof n === 'string' ? n : n.region_id || n.id || n).slice(0, 10)
}

function formatLastCycle(ts) {
  if (!ts) return 'N/A'
  try {
    return new Date(ts).toLocaleString()
  } catch { return ts }
}

watch(selectedTier, () => { renderMarkers(); renderEdges() })
watch(showIntercomm, () => renderEdges())
watch(topologyData, () => { renderMarkers(); renderEdges() })

onMounted(async () => {
  await agentStore.fetchAgents()
  await loadTopology()

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
  <ProjectLayout>
    <div class="agent-map">
      <div class="map-header glass">
        <div class="header-left">
          <h2>Agent Map</h2>
          <span class="agent-badge">{{ totalAgents }} agents</span>
        </div>
        <div class="header-controls">
          <button
            class="toggle-btn"
            :class="{ active: showIntercomm }"
            @click="toggleIntercomm"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Show Intercommunication
          </button>
          <div class="tier-filters">
            <button
              v-for="t in ['all', '1', '2', '3']"
              :key="t"
              class="tier-btn"
              :class="{ active: selectedTier === t }"
              @click="setTier(t)"
            >
              {{ TIER_LABELS[t] }}
            </button>
          </div>
        </div>
      </div>

      <div class="map-body">
        <div ref="mapContainer" class="map-container"></div>

        <div class="map-legend">
          <span class="legend-title">Severity</span>
          <span v-for="(color, sev) in SEVERITY_COLORS" :key="sev" class="legend-item">
            <span class="legend-dot" :style="{ background: color }"></span>
            {{ sev }}
          </span>
          <span class="legend-title tier-title">Tier Size</span>
          <span class="legend-item">
            <span class="legend-circle t1"></span>
            T1 (Regional)
          </span>
          <span class="legend-item">
            <span class="legend-circle t2"></span>
            T2 (Cluster)
          </span>
          <span class="legend-item">
            <span class="legend-circle t3"></span>
            T3 (Port/Node)
          </span>
        </div>

        <Transition name="panel">
          <div v-if="selectedAgent" class="detail-panel">
            <button class="close-btn" @click="closePanel">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <div v-if="panelLoading" class="panel-state">
              <span class="loading-spinner"></span>
              <span>Loading agent data...</span>
            </div>
            <div v-else-if="panelError" class="panel-state error">
              {{ panelError }}
            </div>
            <AgentDetailCard v-else :agent="selectedAgent" />
          </div>
        </Transition>
      </div>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.agent-map {
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
  border-bottom: 1px solid var(--color-border);
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.header-left h2 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
}

.agent-badge {
  font-size: var(--text-xs);
  font-weight: 600;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  background: var(--color-primary);
  color: #fff;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toggle-btn:hover {
  border-color: var(--color-border-hover);
  color: var(--color-text);
}

.toggle-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.tier-filters {
  display: flex;
  gap: var(--spacing-1);
}

.tier-btn {
  padding: var(--spacing-1) var(--spacing-3);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tier-btn:hover {
  border-color: var(--color-border-hover);
  color: var(--color-text);
}

.tier-btn.active {
  background: var(--color-bg-tertiary);
  border-color: var(--color-primary);
  color: var(--color-primary-light);
}

.map-body {
  flex: 1;
  position: relative;
  display: flex;
}

.map-container {
  flex: 1;
  min-height: 400px;
  background-color: var(--color-bg);
}

.map-legend {
  position: absolute;
  bottom: var(--spacing-4);
  left: var(--spacing-4);
  background: rgba(15, 22, 35, 0.9);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-3) var(--spacing-4);
  z-index: 500;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.legend-title {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-tertiary);
  margin-top: var(--spacing-1);
}

.tier-title {
  margin-top: var(--spacing-2);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-circle {
  border-radius: 50%;
  flex-shrink: 0;
  border: 1px solid rgba(255,255,255,0.2);
}

.legend-circle.t1 { width: 16px; height: 16px; }
.legend-circle.t2 { width: 12px; height: 12px; }
.legend-circle.t3 { width: 8px; height: 8px; }

.detail-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 300px;
  height: 100%;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
}

.panel-header h3 {
  margin: 0 0 var(--spacing-1);
  font-size: var(--text-lg);
  font-weight: 600;
}

.tier-tag {
  font-size: var(--text-xs);
  font-weight: 600;
  padding: 0.15rem 0.4rem;
  border-radius: var(--radius-sm);
  background: var(--color-bg-tertiary);
  color: var(--color-primary-light);
  letter-spacing: 0.03em;
}

.close-btn {
  position: absolute;
  top: var(--spacing-3);
  right: var(--spacing-3);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  cursor: pointer;
  color: var(--color-text-secondary);
  flex-shrink: 0;
  transition: all var(--transition-fast);
  z-index: 10;
}

.close-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-4);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-row--col {
  flex-direction: column;
  align-items: flex-start;
  gap: var(--spacing-2);
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.stat-value {
  font-size: var(--text-sm);
  font-weight: 500;
}

.text-mono { font-family: var(--font-mono); }
.text-success { color: var(--color-success); }
.text-tertiary { color: var(--color-text-tertiary); }
.text-secondary { color: var(--color-text-secondary); }

.locations-list,
.neighbors-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-1);
}

.location-tag,
.neighbor-tag {
  font-size: var(--text-xs);
  padding: 0.15rem 0.4rem;
  border-radius: var(--radius-sm);
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.15rem 0.4rem;
  font-size: var(--text-xs);
  font-weight: 600;
  border-radius: var(--radius-full);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.badge--low { background: var(--color-low-bg); color: var(--color-low); }
.badge--medium { background: var(--color-medium-bg); color: var(--color-medium); }
.badge--high { background: var(--color-high-bg); color: var(--color-high); }
.badge--critical { background: var(--color-critical-bg); color: var(--color-critical); }

/* Panel transition */
.panel-enter-active,
.panel-leave-active {
  transition: transform 200ms ease;
}

.panel-enter-from,
.panel-leave-to {
  transform: translateX(100%);
}

/* Panel loading/error states */
.panel-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-3);
  padding: var(--spacing-6);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  height: 100%;
}

.panel-state.error {
  color: var(--color-error);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Agent marker pulse for running agents */
:global(.agent-marker.running) {
  animation: markerPulse 2s infinite;
}

@keyframes markerPulse {
  0%, 100% { box-shadow: 0 0 6px currentColor; }
  50% { box-shadow: 0 0 14px currentColor, 0 0 20px currentColor; }
}

@media (max-width: 768px) {
  .header-controls { flex-wrap: wrap; gap: var(--spacing-2); }
  .map-legend { display: none; }
  .detail-panel { width: 100%; }
}
</style>