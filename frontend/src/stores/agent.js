// LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
// Copyright (C) 2025 LogiSwarm Contributors
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAgentStore = defineStore('agent', () => {
  const agents = ref([])
  const currentAgent = ref(null)
  const riskMap = ref({})
  const loading = ref(false)
  const error = ref(null)
  const eventSource = ref(null)

  const tierStats = ref({})
  const tierHierarchy = ref({})
  const searchQuery = ref('')
  const selectedTiers = ref([])
  const pagination = ref({ total: 0, limit: 50, offset: 0 })

  const agentCount = computed(() => agents.value.length)
  const agentsByRegion = computed(() => {
    const map = {}
    for (const agent of agents.value) {
      map[agent.region_id] = agent
    }
    return map
  })
  const tier1Agents = computed(() => agents.value.filter(a => a.tier === 1 || (!a.tier && ['se_asia','europe','gulf_suez','north_america','china_ea','south_asia','latin_america','africa'].includes(a.region_id))))
  const tier2Agents = computed(() => agents.value.filter(a => a.tier === 2))
  const tier3Agents = computed(() => agents.value.filter(a => a.tier === 3))
  const highRiskAgents = computed(() => 
    agents.value.filter(a => 
      a.last_assessment?.severity === 'HIGH' || 
      a.last_assessment?.severity === 'CRITICAL'
    )
  )
  const degradedAgents = computed(() =>
    agents.value.filter(a => a.degradation_status?.is_degraded)
  )
  const filteredAgents = computed(() => {
    let filtered = agents.value
    if (selectedTiers.value.length > 0) {
      filtered = filtered.filter(a => selectedTiers.value.includes(a.tier || 1))
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
      pagination.value.total = data.meta?.total || agents.value.length
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchFilteredAgents({ tiers = [], search = '', limit = 50, offset = 0 } = {}) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      if (tiers.length > 0) {
        tiers.forEach(t => params.append('tier', String(t)))
      }
      if (search) params.set('search', search)
      params.set('limit', String(limit))
      params.set('offset', String(offset))
      const url = `/api/agents/list?${params.toString()}`
      const response = await fetch(url)
      const envelope = await response.json()
      if (envelope.error) {
        throw new Error(envelope.error)
      }
      return envelope
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchAgentStats() {
    try {
      const response = await fetch('/api/agents/stats')
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      tierStats.value = data.data || {}
      return data.data
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  async function fetchAgentTiers() {
    try {
      const response = await fetch('/api/agents/tiers')
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      tierHierarchy.value = data.data || {}
      return data.data
    } catch (e) {
      error.value = e.message
      return null
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
    tier1Agents,
    tier2Agents,
    tier3Agents,
    highRiskAgents,
    degradedAgents,
    filteredAgents,
    tierStats,
    tierHierarchy,
    searchQuery,
    selectedTiers,
    pagination,
    fetchAgents,
    fetchFilteredAgents,
    fetchAgentStats,
    fetchAgentTiers,
    fetchAgentStatus,
    fetchAgentConfig,
    updateAgentConfig,
    fetchRiskMap,
    connectToSSE,
    disconnectSSE
  }
})