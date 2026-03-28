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

export const useFeedStore = defineStore('feed', () => {
  const degradationStatuses = ref([])
  const loading = ref(false)
  const error = ref(null)

  const isAnyDegraded = computed(() => {
    return degradationStatuses.value.some(
      s => s.mode === 'DEGRADED' || s.mode === 'OFFLINE'
    )
  })

  const degradedRegions = computed(() => {
    return degradationStatuses.value.filter(
      s => s.mode === 'DEGRADED' || s.mode === 'OFFLINE'
    )
  })

  const offlineRegions = computed(() => {
    return degradationStatuses.value.filter(s => s.mode === 'OFFLINE')
  })

  async function fetchDegradationStatus() {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/agents/degradation-status')
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      degradationStatuses.value = data.data || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchRegionDegradationStatus(regionId) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/agents/${regionId}/degradation-status`)
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

  return {
    degradationStatuses,
    loading,
    error,
    isAnyDegraded,
    degradedRegions,
    offlineRegions,
    fetchDegradationStatus,
    fetchRegionDegradationStatus
  }
})