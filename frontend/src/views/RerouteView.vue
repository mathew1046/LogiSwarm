<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'
import { useRerouteStore } from '@/stores/reroute'
import { useToast } from '@/composables/useToast'
import ReasoningTerminal from '@/components/routing/ReasoningTerminal.vue'
import ComparisonCard from '@/components/routing/ComparisonCard.vue'

const rerouteStore = useRerouteStore()
const toast = useToast()

const mapContainer = ref(null)
const map = ref(null)
const routeLayers = ref([])

const shipmentRef = ref('')
const currentRouteId = ref('')
const proposedRouteId = ref('')
const reason = ref('')

const canAnalyze = computed(() => {
  return currentRouteId.value && proposedRouteId.value && !rerouteStore.analyzing
})

const canExecute = computed(() => {
  return rerouteStore.hasAnalysis && !rerouteStore.executing
})

function getRouteById(id) {
  return rerouteStore.routes.find(r => r.id === id) || null
}

const currentRoute = computed(() => getRouteById(currentRouteId.value))
const proposedRoute = computed(() => getRouteById(proposedRouteId.value))

function clearRouteLayers() {
  if (map.value && routeLayers.value.length) {
    routeLayers.value.forEach(layer => layer.remove())
    routeLayers.value = []
  }
}

function drawRoutes() {
  if (!map.value || !window.L) return
  clearRouteLayers()

  const current = currentRoute.value
  const proposed = proposedRoute.value

  if (current?.path?.coordinates) {
    const coords = current.path.coordinates.map(c => [c[1], c[0]])
    const polyline = window.L.polyline(coords, {
      color: '#ef4444',
      weight: 4,
      opacity: 0.8
    }).addTo(map.value)
    routeLayers.value.push(polyline)
  }

  if (proposed?.path?.coordinates) {
    const coords = proposed.path.coordinates.map(c => [c[1], c[0]])
    const polyline = window.L.polyline(coords, {
      color: '#22c55e',
      weight: 4,
      opacity: 0.8
    }).addTo(map.value)
    routeLayers.value.push(polyline)
  }

  if (routeLayers.value.length) {
    const group = window.L.featureGroup(routeLayers.value)
    map.value.fitBounds(group.getBounds(), { padding: [50, 50] })
  }
}

function initMap() {
  if (!mapContainer.value || typeof window === 'undefined' || !window.L) return

  map.value = window.L.map(mapContainer.value, {
    center: [20, 0],
    zoom: 2,
    minZoom: 1,
    maxZoom: 10
  })

  window.L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19,
    noWrap: true
  }).addTo(map.value)
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
    script.onload = () => {
      window.L = window.L || window['leaflet']
      initMap()
      if (currentRouteId.value || proposedRouteId.value) {
        drawRoutes()
      }
    }
    document.head.appendChild(script)
  } else {
    initMap()
  }
}

async function handleAnalyze() {
  if (!canAnalyze.value) return

  const result = await rerouteStore.analyze({
    shipmentRef: shipmentRef.value || 'SH-UNKNOWN',
    currentRouteId: currentRouteId.value,
    proposedRouteId: proposedRouteId.value,
    reason: reason.value
  })

  if (result) {
    toast.success('Analysis complete')
    drawRoutes()
  } else {
    toast.error(rerouteStore.error || 'Analysis failed')
  }
}

async function handleExecute() {
  if (!canExecute.value || !rerouteStore.currentAnalysis) return

  const result = await rerouteStore.execute({
    analysisId: rerouteStore.currentAnalysis.analysis_id,
    shipmentRef: rerouteStore.currentAnalysis.shipment_ref,
    newRouteId: proposedRouteId.value,
    approvedBy: 'operator@logiswarm.io'
  })

  if (result) {
    toast.success('Reroute executed successfully')
  } else {
    toast.error(rerouteStore.error || 'Execute failed')
  }
}

function handleClear() {
  shipmentRef.value = ''
  currentRouteId.value = ''
  proposedRouteId.value = ''
  reason.value = ''
  clearRouteLayers()
  if (map.value) {
    map.value.setView([20, 0], 2)
  }
}

watch([currentRouteId, proposedRouteId], () => {
  if (map.value && window.L) {
    drawRoutes()
  }
})

onMounted(async () => {
  await rerouteStore.fetchRoutes()
  loadLeaflet()
})

onUnmounted(() => {
  clearRouteLayers()
  if (map.value) {
    map.value.remove()
    map.value = null
  }
})
</script>

<template>
  <ProjectLayout>
    <div class="reroute-page">
      <div class="reroute-header">
        <h1>Reroute Decision Support</h1>
        <p class="header-subtitle">Analyze alternative routes and execute reroutes with LLM-powered reasoning</p>
      </div>

      <div class="reroute-grid">
        <div class="panel panel--left">
          <div class="card">
            <div class="card-label">Route Selection</div>
            <div class="form-grid">
              <div class="form-group">
                <label class="label">Shipment Reference</label>
                <input
                  v-model="shipmentRef"
                  type="text"
                  class="input"
                  placeholder="SH-12345"
                />
              </div>
              <div class="form-group">
                <label class="label">Current Route</label>
                <select v-model="currentRouteId" class="input">
                  <option value="">Select current route...</option>
                  <option v-for="route in rerouteStore.routes" :key="route.id" :value="route.id">
                    {{ route.name || route.id }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label class="label">Proposed Route</label>
                <select v-model="proposedRouteId" class="input">
                  <option value="">Select proposed route...</option>
                  <option v-for="route in rerouteStore.routes" :key="route.id" :value="route.id">
                    {{ route.name || route.id }}
                  </option>
                </select>
              </div>
              <div class="form-group form-group--full">
                <label class="label">Reason for Analysis</label>
                <input
                  v-model="reason"
                  type="text"
                  class="input"
                  placeholder="Suez Canal congestion, weather disruption, etc."
                />
              </div>
            </div>
            <div class="action-row">
              <button
                class="btn btn--primary"
                :disabled="!canAnalyze"
                @click="handleAnalyze"
              >
                <svg v-if="rerouteStore.analyzing" class="btn-spinner" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                </svg>
                {{ rerouteStore.analyzing ? 'Analyzing...' : 'Analyze' }}
              </button>
              <button class="btn btn--secondary" @click="handleClear">Clear</button>
            </div>
          </div>

          <div class="card map-card">
            <div class="card-label">Route Map</div>
            <div ref="mapContainer" class="map-container"></div>
            <div class="map-legend">
              <span class="legend-item">
                <span class="legend-color legend-color--current"></span>
                <span class="legend-label">Current</span>
              </span>
              <span class="legend-item">
                <span class="legend-color legend-color--proposed"></span>
                <span class="legend-label">Proposed</span>
              </span>
            </div>
          </div>
        </div>

        <div class="panel panel--right">
          <div class="card reasoning-card">
            <ReasoningTerminal
              :reasoning="rerouteStore.currentAnalysis?.reasoning || ''"
              :confidence="rerouteStore.currentAnalysis?.confidence ?? null"
              :recommendation="rerouteStore.currentAnalysis?.recommendation || null"
              :loading="rerouteStore.analyzing"
            />
          </div>

          <div class="card comparison-card-wrapper">
            <ComparisonCard
              :currentRoute="currentRoute"
              :proposedRoute="proposedRoute"
              :deltaCost="rerouteStore.currentAnalysis?.delta_cost ?? null"
              :deltaTransitHours="rerouteStore.currentAnalysis?.delta_transit_hours ?? null"
              :deltaReliability="rerouteStore.currentAnalysis?.delta_reliability ?? null"
            />
          </div>

          <div v-if="rerouteStore.hasAnalysis" class="execute-section">
            <button
              class="btn btn--primary btn--lg"
              :disabled="!canExecute"
              @click="handleExecute"
            >
              <svg v-if="rerouteStore.executing" class="btn-spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
              </svg>
              {{ rerouteStore.executing ? 'Executing...' : 'Execute Reroute' }}
            </button>
            <p class="execute-note">Requires operator authentication</p>
          </div>

          <div v-if="rerouteStore.hasExecution" class="execution-result">
            <div class="result-badge result-badge--success">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              Reroute executed: {{ rerouteStore.executionResult?.shipment_ref }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.reroute-page {
  padding: 0;
}

.reroute-header {
  margin-bottom: var(--spacing-6);
}

.reroute-header h1 {
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 var(--spacing-2);
}

.header-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin: 0;
}

.reroute-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-6);
  align-items: start;
}

@media (max-width: 1024px) {
  .reroute-grid {
    grid-template-columns: 1fr;
  }
}

.panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
}

.card-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-4);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.form-group--full {
  grid-column: 1 / -1;
}

.input {
  width: 100%;
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: var(--text-sm);
  transition: border-color var(--transition-fast);
}

.input:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

select.input {
  cursor: pointer;
}

.action-row {
  display: flex;
  gap: var(--spacing-3);
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  font-size: var(--text-sm);
  font-weight: 500;
  border-radius: var(--radius-md);
  border: none;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn--primary {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: var(--color-text-inverse);
}

.btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 0 24px var(--color-primary-glow);
}

.btn--secondary {
  background: transparent;
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.btn--secondary:hover:not(:disabled) {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-hover);
}

.btn--lg {
  padding: var(--spacing-3) var(--spacing-6);
  font-size: var(--text-base);
}

.btn-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.map-card {
  padding: var(--spacing-4);
}

.map-container {
  height: 300px;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.map-legend {
  display: flex;
  gap: var(--spacing-4);
  margin-top: var(--spacing-3);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--color-border);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.legend-color {
  width: 12px;
  height: 3px;
  border-radius: 2px;
}

.legend-color--current {
  background: #ef4444;
}

.legend-color--proposed {
  background: #22c55e;
}

.legend-label {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.reasoning-card {
  padding: 0;
  overflow: hidden;
}

.comparison-card-wrapper {
  padding: 0;
  overflow: hidden;
}

.execute-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.execute-note {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: 0;
}

.execution-result {
  padding: var(--spacing-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.result-badge {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-sm);
  font-weight: 500;
}

.result-badge--success {
  color: var(--color-low);
}
</style>