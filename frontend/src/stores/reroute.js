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

export const useRerouteStore = defineStore('reroute', () => {
  // State
  const routes = ref([])
  const currentAnalysis = ref(null)
  const executionResult = ref(null)
  const loading = ref(false)
  const analyzing = ref(false)
  const executing = ref(false)
  const error = ref(null)

  // Getters
  const hasAnalysis = computed(() => currentAnalysis.value !== null)
  const hasExecution = computed(() => executionResult.value !== null)
  const analysisConfidence = computed(() => currentAnalysis.value?.confidence ?? null)
  const recommendation = computed(() => currentAnalysis.value?.recommendation ?? null)

  // Actions
  async function fetchRoutes() {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/routes')
      const envelope = await response.json()
      if (envelope.error) {
        throw new Error(envelope.error)
      }
      routes.value = envelope.data?.routes || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function analyze({ shipmentRef, currentRouteId, proposedRouteId, reason }) {
    analyzing.value = true
    error.value = null
    currentAnalysis.value = null
    try {
      const response = await fetch('/api/reroute/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          shipment_ref: shipmentRef,
          current_route_id: currentRouteId,
          proposed_route_id: proposedRouteId,
          reason: reason || ''
        })
      })
      const envelope = await response.json()
      if (envelope.error) {
        throw new Error(envelope.error)
      }
      currentAnalysis.value = envelope.data
      return envelope.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      analyzing.value = false
    }
  }

  async function execute({ analysisId, shipmentRef, newRouteId, approvedBy }) {
    executing.value = true
    error.value = null
    executionResult.value = null
    try {
      const response = await fetch('/api/reroute/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          analysis_id: analysisId,
          shipment_ref: shipmentRef,
          new_route_id: newRouteId,
          approved_by: approvedBy
        })
      })
      const envelope = await response.json()
      if (envelope.error) {
        throw new Error(envelope.error)
      }
      executionResult.value = envelope.data
      return envelope.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      executing.value = false
    }
  }

  function clearAnalysis() {
    currentAnalysis.value = null
    executionResult.value = null
    error.value = null
  }

  return {
    // State
    routes,
    currentAnalysis,
    executionResult,
    loading,
    analyzing,
    executing,
    error,
    // Getters
    hasAnalysis,
    hasExecution,
    analysisConfidence,
    recommendation,
    // Actions
    fetchRoutes,
    analyze,
    execute,
    clearAnalysis
  }
})