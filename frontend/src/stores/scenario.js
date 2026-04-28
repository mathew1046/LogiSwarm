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
import { useAuthStore } from './auth'

export const useScenarioStore = defineStore('scenario', () => {
  const scenarios = ref([])
  const selectedScenario = ref(null)
  const categories = ref([])
  const loading = ref(false)
  const error = ref(null)

  const scenariosByCategory = computed(() => {
    const map = {}
    for (const scenario of scenarios.value) {
      const category = scenario.category || 'unknown'
      if (!map[category]) {
        map[category] = []
      }
      map[category].push(scenario)
    }
    return map
  })

  const criticalScenarios = computed(() =>
    scenarios.value.filter(s =>
      s.severity === 'CRITICAL' || s.severity === 'HIGH'
    )
  )

  async function fetchScenarios({ category = null, limit = 20, offset = 0 } = {}) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      if (category) params.set('category', category)
      params.set('limit', String(limit))
      params.set('offset', String(offset))
      const url = `/api/scenarios?${params.toString()}`
      const response = await fetch(url)
      const envelope = await response.json()
      if (envelope.error) {
        throw new Error(envelope.error)
      }
      scenarios.value = envelope.data || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchScenarioDetail(scenarioId) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/scenarios/${scenarioId}`)
      const envelope = await response.json()
      if (envelope.error) {
        throw new Error(envelope.error)
      }
      selectedScenario.value = envelope.data
      return envelope.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function runScenario(scenarioId) {
    loading.value = true
    error.value = null
    try {
      const authStore = useAuthStore()
      const response = await fetch(`/api/scenarios/${scenarioId}/run`, {
        method: 'POST',
        headers: authStore.getAuthHeaders()
      })
      const envelope = await response.json()
      if (envelope.error) {
        throw new Error(envelope.error)
      }
      return envelope.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchCategories() {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/scenarios/categories')
      const envelope = await response.json()
      if (envelope.error) {
        throw new Error(envelope.error)
      }
      categories.value = envelope.data || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return {
    scenarios,
    selectedScenario,
    categories,
    loading,
    error,
    scenariosByCategory,
    criticalScenarios,
    fetchScenarios,
    fetchScenarioDetail,
    runScenario,
    fetchCategories
  }
})