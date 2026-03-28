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