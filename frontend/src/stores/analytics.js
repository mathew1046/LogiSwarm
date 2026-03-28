import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAnalyticsStore = defineStore('analytics', () => {
  const summary = ref(null)
  const timeline = ref([])
  const severityDistribution = ref([])
  const regionMetrics = ref([])
  const accuracyTimeline = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchAll(timeRange = '30d') {
    loading.value = true
    error.value = null

    try {
      const [summaryRes, timelineRes, severityRes, metricsRes, accuracyRes] = await Promise.all([
        fetch(`/api/analytics/summary?time_range=${timeRange}`),
        fetch(`/api/analytics/disruptions/timeline?time_range=${timeRange}`),
        fetch(`/api/analytics/severity/distribution?time_range=${timeRange}`),
        fetch(`/api/analytics/regions/metrics?time_range=${timeRange}`),
        fetch(`/api/analytics/accuracy/timeline?time_range=${timeRange}`)
      ])

      const summaryData = await summaryRes.json()
      const timelineData = await timelineRes.json()
      const severityData = await severityRes.json()
      const metricsData = await metricsRes.json()
      const accuracyData = await accuracyRes.json()

      if (summaryData.error) throw new Error(summaryData.error)
      if (timelineData.error) throw new Error(timelineData.error)
      if (severityData.error) throw new Error(severityData.error)
      if (metricsData.error) throw new Error(metricsData.error)
      if (accuracyData.error) throw new Error(accuracyData.error)

      summary.value = summaryData.data
      timeline.value = timelineData.data || []
      severityDistribution.value = severityData.data || []
      regionMetrics.value = metricsData.data || []
      accuracyTimeline.value = accuracyData.data || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchTimeline(timeRange = '30d') {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/analytics/disruptions/timeline?time_range=${timeRange}`)
      const data = await response.json()
      if (data.error) throw new Error(data.error)
      timeline.value = data.data || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchSeverityDistribution(timeRange = '30d') {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/analytics/severity/distribution?time_range=${timeRange}`)
      const data = await response.json()
      if (data.error) throw new Error(data.error)
      severityDistribution.value = data.data || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchRegionMetrics(timeRange = '30d') {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/analytics/regions/metrics?time_range=${timeRange}`)
      const data = await response.json()
      if (data.error) throw new Error(data.error)
      regionMetrics.value = data.data || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  function getOffset(index) {
    let offset = 0
    for (let i = 0; i < index; i++) {
      offset += (severityDistribution.value[i]?.percentage || 0) * 4.4
    }
    return offset
  }

  function getDecisionPercent(type) {
    const breakdown = summary.value?.decision_breakdown
    if (!breakdown || breakdown.total === 0) return 0
    return ((breakdown[type] || 0) / breakdown.total) * 100
  }

  return {
    summary,
    timeline,
    severityDistribution,
    regionMetrics,
    accuracyTimeline,
    loading,
    error,
    fetchAll,
    fetchTimeline,
    fetchSeverityDistribution,
    fetchRegionMetrics,
    getOffset,
    getDecisionPercent
  }
})