<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'
import { useSimpleAppStore } from '@/stores/simpleApp'

const simpleAppStore = useSimpleAppStore()

const mapContainer = ref(null)
const map = ref(null)
const markersLayer = ref(null)
const selectedAgentId = ref(null)

const agents = computed(() => simpleAppStore.agents)
const topology = computed(() => simpleAppStore.topology)
const selectedAgent = computed(() => agents.value.find(agent => agent.agent_id === selectedAgentId.value) || null)

const severityColors = {
  LOW: '#22c55e',
  MEDIUM: '#eab308',
  HIGH: '#f97316',
  CRITICAL: '#ef4444'
}

function colorForSeverity(severity) {
  return severityColors[(severity || 'LOW').toUpperCase()] || severityColors.LOW
}

function loadLeaflet() {
  if (typeof window === 'undefined') return

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

function initMap() {
  if (!mapContainer.value || typeof window === 'undefined' || !window.L) return
  if (map.value) return

  map.value = window.L.map(mapContainer.value, {
    center: [20, 0],
    zoom: 2,
    minZoom: 1,
    maxZoom: 10,
    worldCopyJump: true
  })

  window.L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19,
    noWrap: true
  }).addTo(map.value)

  markersLayer.value = window.L.layerGroup().addTo(map.value)
  renderMarkers()
}

function renderMarkers() {
  if (!map.value || !window.L || !markersLayer.value) return

  markersLayer.value.clearLayers()

  topology.value.nodes?.forEach(node => {
    const selected = selectedAgentId.value === `agent-${node.id}`
    const color = colorForSeverity(node.severity)

    const icon = window.L.divIcon({
      className: '',
      html: `<div style="
        width: ${selected ? 18 : 14}px;
        height: ${selected ? 18 : 14}px;
        background: ${color};
        border-radius: 50%;
        border: ${selected ? '3px solid #ffffff' : '2px solid rgba(255,255,255,0.45)'};
        box-shadow: 0 0 14px ${color}99;
      "></div>`,
      iconSize: [selected ? 18 : 14, selected ? 18 : 14],
      iconAnchor: [selected ? 9 : 7, selected ? 9 : 7]
    })

    const marker = window.L.marker([node.lat, node.lon], { icon })
    marker.on('click', () => {
      selectedAgentId.value = `agent-${node.id}`
    })
    marker.bindTooltip(node.label, { direction: 'top' })
    markersLayer.value.addLayer(marker)
  })
}

watch([topology, selectedAgentId], () => {
  renderMarkers()
})

onMounted(async () => {
  await simpleAppStore.bootstrap()
  await simpleAppStore.fetchAgents()
  loadLeaflet()
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
    <div class="page-stack">
      <div class="page-header">
        <h1>Agents</h1>
        <p class="muted">10 global agents shown on a world map. Click a marker to inspect the agent’s mocked weather, news, risk, and reasoning.</p>
      </div>

      <div class="map-grid">
        <div class="card map-card">
          <div class="card-label">World Agent Map</div>
          <div ref="mapContainer" class="map-container"></div>
          <div class="legend-row">
            <span v-for="(color, severity) in severityColors" :key="severity" class="legend-item">
              <span class="legend-dot" :style="{ background: color }"></span>
              {{ severity }}
            </span>
          </div>
        </div>

        <div class="card detail-card">
          <div class="card-label">Agent Details</div>
          <div v-if="selectedAgent">
            <div class="detail-top">
              <div>
                <h2>{{ selectedAgent.place_name }}</h2>
                <p class="muted">{{ selectedAgent.region }}</p>
              </div>
              <span class="badge" :class="`badge--${selectedAgent.severity.toLowerCase()}`">{{ selectedAgent.severity }}</span>
            </div>
            <div class="metric-row">
              <span>Risk Score</span>
              <strong>{{ selectedAgent.risk_score }}</strong>
            </div>
            <div class="info-block">
              <strong>Weather</strong>
              <p>{{ selectedAgent.weather }}</p>
            </div>
            <div class="info-block">
              <strong>News</strong>
              <p>{{ selectedAgent.news }}</p>
            </div>
            <div class="info-block">
              <strong>Reasoning</strong>
              <p>{{ selectedAgent.reasoning }}</p>
            </div>
            <div class="info-block">
              <strong>Neighbors</strong>
              <p>{{ selectedAgent.neighbors.join(', ') }}</p>
            </div>
          </div>
          <div v-else class="empty-detail muted">
            Click an agent marker to see its information.
          </div>
        </div>
      </div>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.page-stack { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; flex-direction: column; gap: 0.35rem; }
.muted { color: var(--color-text-secondary); }
.map-grid { display: grid; grid-template-columns: minmax(0, 2fr) minmax(320px, 1fr); gap: 1rem; }
.map-card, .detail-card { display: flex; flex-direction: column; gap: 0.9rem; }
.map-container { height: 560px; border-radius: var(--radius-lg); overflow: hidden; border: 1px solid var(--color-border); }
.legend-row { display: flex; flex-wrap: wrap; gap: 0.75rem; }
.legend-item { display: inline-flex; align-items: center; gap: 0.35rem; color: var(--color-text-secondary); font-size: 0.85rem; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.detail-top, .metric-row { display: flex; justify-content: space-between; gap: 1rem; }
.info-block { display: flex; flex-direction: column; gap: 0.25rem; padding-top: 0.5rem; border-top: 1px solid var(--color-border); }
.empty-detail { display: flex; align-items: center; justify-content: center; min-height: 240px; }
@media (max-width: 980px) {
  .map-grid { grid-template-columns: 1fr; }
  .map-container { height: 420px; }
}
</style>
