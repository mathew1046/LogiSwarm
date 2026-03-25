import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAgentStore = defineStore('agent', () => {
  const agents = ref([])
  const currentAgent = ref(null)
  const riskMap = ref({})
  const loading = ref(false)
  const error = ref(null)
  const eventSource = ref(null)

  const agentCount = computed(() => agents.value.length)
  const agentsByRegion = computed(() => {
    const map = {}
    for (const agent of agents.value) {
      map[agent.region_id] = agent
    }
    return map
  })
  const highRiskAgents = computed(() => 
    agents.value.filter(a => 
      a.last_assessment?.severity === 'HIGH' || 
      a.last_assessment?.severity === 'CRITICAL'
    )
  )

  async function fetchAgents() {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/agents')
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      agents.value = data.data || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchAgentStatus(regionId) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/agents/${regionId}/status`)
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      currentAgent.value = data.data
      return data.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchAgentConfig(regionId) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/agents/${regionId}/config`)
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      return data.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateAgentConfig(regionId, config) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/agents/${regionId}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      })
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      return data.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchRiskMap() {
    try {
      const response = await fetch('/api/orchestrator/risk-map')
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      riskMap.value = data.data || {}
    } catch (e) {
      error.value = e.message
    }
  }

  function connectToSSE() {
    if (eventSource.value) {
      eventSource.value.close()
    }
    
    eventSource.value = new EventSource('/api/agents/stream')
    
    eventSource.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleSSEEvent(data)
      } catch (e) {
        console.error('Failed to parse SSE event:', e)
      }
    }
    
    eventSource.value.onerror = (e) => {
      console.error('SSE connection error:', e)
    }
  }

  function disconnectSSE() {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
  }

  function handleSSEEvent(data) {
    const { event_type, region_id, data: payload } = data
    
    if (event_type === 'agent_assessment' && region_id) {
      const agentIndex = agents.value.findIndex(a => a.region_id === region_id)
      if (agentIndex !== -1) {
        agents.value[agentIndex] = {
          ...agents.value[agentIndex],
          last_assessment: payload,
          last_cycle_at: payload.timestamp || new Date().toISOString()
        }
      }
    } else if (event_type === 'cascade_update') {
      fetchRiskMap()
    }
  }

  return {
    agents,
    currentAgent,
    riskMap,
    loading,
    error,
    agentCount,
    agentsByRegion,
    highRiskAgents,
    fetchAgents,
    fetchAgentStatus,
    fetchAgentConfig,
    updateAgentConfig,
    fetchRiskMap,
    connectToSSE,
    disconnectSSE
  }
})