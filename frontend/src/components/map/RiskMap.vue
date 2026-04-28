<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { useThemeStore } from '@/stores/theme'

const mapContainer = ref(null)
const selectedRegion = ref(null)
const map = ref(null)
const layers = ref({})
const baseLayer = ref(null)

const agentStore = useAgentStore()
const themeStore = useThemeStore()
const riskMap = computed(() => agentStore.riskMap)
const isDark = computed(() => themeStore.isDark())

const REGIONS = {
  se_asia: {
    name: 'SE Asia',
    bbox: [[-10, 95], [25, 140]],
    center: [7.5, 117.5]
  },
  europe: {
    name: 'Europe',
    bbox: [[35, -10], [70, 40]],
    center: [52.5, 15]
  },
  gulf_suez: {
    name: 'Gulf/Suez',
    bbox: [[12, 25], [38, 65]],
    center: [25, 45]
  },
  north_america: {
    name: 'North America',
    bbox: [[15, -170], [70, -50]],
    center: [42.5, -110]
  },
  china_ea: {
    name: 'China/East Asia',
    bbox: [[15, 100], [55, 150]],
    center: [35, 125]
  }
}

function getRiskColor(severity) {
  const colors = {
    low: '#22c55e',
    medium: '#f59e0b',
    high: '#f97316',
    critical: '#ef4444'
  }
  return colors[(severity || 'low').toLowerCase()] || colors.low
}

function getRiskOpacity(confidence) {
  const base = 0.3
  const max = 0.7
  const c = confidence || 0.5
  return base + (max - base) * c
}

function darkenColor(hex, factor) {
  const num = parseInt(hex.slice(1), 16)
  const amt = Math.round(2.55 * factor)
  const R = Math.max(0, (num >> 16) - amt)
  const G = Math.max(0, ((num >> 8) & 0x00FF) - amt)
  const B = Math.max(0, (num & 0x0000FF) - amt)
  return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1)
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
  updateRegions()
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

function updateRegions() {
  if (!map.value || typeof window === 'undefined') return

  const L = window.L
  if (!L) return

  Object.entries(REGIONS).forEach(([regionId, config]) => {
    if (layers.value[regionId]) {
      layers.value[regionId].remove()
    }

    const assessment = riskMap.value[regionId] || {}
    const severity = (assessment.severity || 'low').toLowerCase()
    const confidence = assessment.confidence || 0.5
    const color = getRiskColor(severity)
    const opacity = getRiskOpacity(confidence)

    const polygon = L.rectangle(config.bbox, {
      color: darkenColor(color, 20),
      weight: 2,
      fillColor: color,
      fillOpacity: opacity
    })

    polygon.bindPopup(`
      <div class="region-popup">
        <h3>${config.name}</h3>
        <p><strong>Risk Level:</strong> ${severity.toUpperCase()}</p>
        <p><strong>Confidence:</strong> ${(confidence * 100).toFixed(1)}%</p>
      </div>
    `)

    polygon.on('click', () => {
      selectedRegion.value = regionId
    })

    polygon.addTo(map.value)
    layers.value[regionId] = polygon
  })
}

function handleSSEUpdate() {
  updateRegions()
}

watch(riskMap, () => {
  updateRegions()
}, { deep: true })

watch(isDark, () => {
  updateBaseLayer()
})

onMounted(async () => {
  await agentStore.fetchRiskMap()

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
      <h2>Global Risk Map</h2>
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

    <div ref="mapContainer" class="map-container"></div>

    <div v-if="selectedRegion" class="region-detail card card--glass">
      <button class="close-btn" @click="selectedRegion = null">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <h3>{{ REGIONS[selectedRegion]?.name || selectedRegion }}</h3>
      <div class="detail-stats">
        <div class="stat-row">
          <span class="stat-label">Risk Level:</span>
          <span :class="['badge', `badge--${(riskMap[selectedRegion]?.severity || 'low').toLowerCase()}`]">
            {{ (riskMap[selectedRegion]?.severity || 'LOW').toUpperCase() }}
          </span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Confidence:</span>
          <span class="stat-value text-mono">{{ ((riskMap[selectedRegion]?.confidence || 0) * 100).toFixed(1) }}%</span>
        </div>
        <div v-if="riskMap[selectedRegion]?.reasoning" class="stat-row stat-row--full">
          <span class="stat-label">Analysis:</span>
          <p class="stat-text">{{ riskMap[selectedRegion].reasoning }}</p>
        </div>
      </div>
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
  border-bottom: 1px solid var(--color-border);
  z-index: 10;
}

.map-header h2 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
}

.map-legend {
  display: flex;
  gap: var(--spacing-4);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
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
  color: var(--color-text-secondary);
}

.map-container {
  flex: 1;
  min-height: 400px;
  background-color: var(--color-bg);
}

.region-detail {
  position: absolute;
  bottom: var(--spacing-4);
  right: var(--spacing-4);
  width: 300px;
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
  background-color: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background-color: var(--color-bg-secondary);
  color: var(--color-text);
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
  gap: var(--spacing-3);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-row--full {
  flex-direction: column;
  align-items: flex-start;
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.stat-value {
  font-weight: 600;
}

.stat-text {
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  margin: var(--spacing-1) 0 0;
  color: var(--color-text);
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
</style>
