import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'logiswarm_alerts'

export const useAlertStore = defineStore('alert', () => {
  const alerts = ref([])
  const loading = ref(false)
  const error = ref(null)

  const unreadCount = computed(() => 
    alerts.value.filter(a => !a.read).length
  )
  const unhandledAlerts = computed(() => 
    alerts.value.filter(a => !a.handled && !a.dismissed)
  )
  const criticalAlerts = computed(() => 
    alerts.value.filter(a => a.severity === 'CRITICAL' && !a.dismissed)
  )

  function loadFromStorage() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        alerts.value = JSON.parse(stored)
      }
    } catch (e) {
      console.error('Failed to load alerts from storage:', e)
    }
  }

  function saveToStorage() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(alerts.value))
    } catch (e) {
      console.error('Failed to save alerts to storage:', e)
    }
  }

  function addAlert(alert) {
    const newAlert = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2),
      timestamp: new Date().toISOString(),
      read: false,
      handled: false,
      dismissed: false,
      ...alert
    }
    alerts.value.unshift(newAlert)
    saveToStorage()
    return newAlert
  }

  function markAsRead(alertId) {
    const alert = alerts.value.find(a => a.id === alertId)
    if (alert) {
      alert.read = true
      saveToStorage()
    }
  }

  function markAllAsRead() {
    for (const alert of alerts.value) {
      alert.read = true
    }
    saveToStorage()
  }

  function handleAlert(alertId, decision) {
    const alert = alerts.value.find(a => a.id === alertId)
    if (alert) {
      alert.handled = true
      alert.handledAt = new Date().toISOString()
      alert.decision = decision
      saveToStorage()
    }
  }

  function dismissAlert(alertId) {
    const alert = alerts.value.find(a => a.id === alertId)
    if (alert) {
      alert.dismissed = true
      saveToStorage()
    }
  }

  function clearAll() {
    alerts.value = []
    saveToStorage()
  }

  function clearHandled() {
    alerts.value = alerts.value.filter(a => !a.handled && !a.dismissed)
    saveToStorage()
  }

  async function fetchDecisions(projectId, limit = 50) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/decisions?project_id=${projectId}&limit=${limit}`)
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      return data.data?.decisions || []
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function submitFeedback(decisionId, payload) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/decisions/${decisionId}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
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

  function initialize() {
    loadFromStorage()
  }

  return {
    alerts,
    loading,
    error,
    unreadCount,
    unhandledAlerts,
    criticalAlerts,
    addAlert,
    markAsRead,
    markAllAsRead,
    handleAlert,
    dismissAlert,
    clearAll,
    clearHandled,
    fetchDecisions,
    submitFeedback,
    initialize
  }
})