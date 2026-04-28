import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export const useSimpleAppStore = defineStore('simpleApp', () => {
  const places = ref([])
  const shipment = ref(null)
  const routePlan = ref(null)
  const agents = ref([])
  const topology = ref({ nodes: [], edges: [] })
  const simulation = ref({ status: 'idle', changes: [], metrics: {} })
  const reports = ref([])
  const loading = ref(false)
  const error = ref(null)

  const hasShipment = computed(() => !!shipment.value)
  const hasRoutePlan = computed(() => !!routePlan.value)
  const hasActiveSimulation = computed(() => simulation.value?.status === 'active')
  const recommendedRoute = computed(() => routePlan.value?.recommended_route || null)

  async function request(url, options = {}) {
    const response = await fetch(url, options)
    const envelope = await response.json()
    if (!response.ok) {
      throw new Error(envelope?.detail || envelope?.error || `Request failed (${response.status})`)
    }
    if (envelope.error) {
      throw new Error(envelope.error)
    }
    return envelope.data
  }

  async function bootstrap() {
    loading.value = true
    error.value = null
    try {
      const [placesData, dashboardData, agentsData, topologyData, reportsData] = await Promise.all([
        request('/api/places'),
        request('/api/dashboard'),
        request('/api/agents'),
        request('/api/agents/topology'),
        request('/api/reports'),
      ])
      places.value = placesData || []
      shipment.value = dashboardData?.shipment || null
      routePlan.value = dashboardData?.route_plan || null
      simulation.value = dashboardData?.simulation || { status: 'idle', changes: [], metrics: {} }
      agents.value = agentsData || []
      topology.value = topologyData || { nodes: [], edges: [] }
      reports.value = reportsData || []
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  async function saveShipment(origin, destination) {
    loading.value = true
    error.value = null
    try {
      const data = await request('/api/shipments/current', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ origin, destination })
      })
      shipment.value = data.shipment
      routePlan.value = data.route_plan
      return data
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchAgents() {
    try {
      agents.value = await request('/api/agents')
      topology.value = await request('/api/agents/topology')
    } catch (err) {
      error.value = err.message
    }
  }

  async function refreshRoutePlan() {
    try {
      routePlan.value = await request('/api/routes/plan')
    } catch (err) {
      error.value = err.message
    }
  }

  async function recomputeRoutes(origin, destination) {
    loading.value = true
    error.value = null
    try {
      routePlan.value = await request('/api/routes/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ origin, destination })
      })
      return routePlan.value
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function startSimulation() {
    loading.value = true
    error.value = null
    try {
      simulation.value = await request('/api/simulation/start', {
        method: 'POST'
      })
      return simulation.value
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function stopSimulation() {
    loading.value = true
    error.value = null
    try {
      simulation.value = await request('/api/simulation/stop', {
        method: 'POST'
      })
      reports.value = await request('/api/reports')
      return simulation.value
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function refreshSimulation() {
    try {
      simulation.value = await request('/api/simulation/status')
      return simulation.value
    } catch (err) {
      error.value = err.message
      return null
    }
  }

  async function fetchReports() {
    try {
      reports.value = await request('/api/reports')
      return reports.value
    } catch (err) {
      error.value = err.message
      return []
    }
  }

  return {
    places,
    shipment,
    routePlan,
    agents,
    topology,
    simulation,
    reports,
    loading,
    error,
    hasShipment,
    hasRoutePlan,
    hasActiveSimulation,
    recommendedRoute,
    bootstrap,
    saveShipment,
    fetchAgents,
    refreshRoutePlan,
    recomputeRoutes,
    startSimulation,
    stopSimulation,
    refreshSimulation,
    fetchReports,
  }
})
