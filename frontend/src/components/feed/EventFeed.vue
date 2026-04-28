<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useAgentStore } from '@/stores/agent'

const props = defineProps({
  maxHeight: {
    type: String,
    default: '600px'
  }
})

const agentStore = useAgentStore()
const events = ref([])
const filterRegion = ref('')
const filterSeverity = ref('')
const filterAction = ref('')
const loading = ref(false)

const filteredEvents = computed(() => {
  return events.value.filter(event => {
    if (filterRegion.value && event.region_id !== filterRegion.value) return false
    if (filterSeverity.value && event.severity !== filterSeverity.value) return false
    if (filterAction.value && event.action_type !== filterAction.value) return false
    return true
  })
})

const regions = computed(() => {
  const regionSet = new Set(events.value.map(e => e.region_id).filter(Boolean))
  return Array.from(regionSet)
})

function getSeverityClass(severity) {
  return `badge--${(severity || 'low').toLowerCase()}`
}

function getActionIcon(actionType) {
  const icons = {
    ALERT: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
    REROUTE: 'M8 7h12m0 0l-4-4m4 4l-4 4M9 17H7a2 2 0 00-2 2v1a2 2 0 002 2h10a2 2 0 002-2v-1a2 2 0 00-2-2h-2M9 17V9m0 8h.01',
    ESCALATE: 'M13 7h8m0 0v-8m0 8c-4.418 0-8-1.79-8-4s3.582-4 8-4 8 1.79 8 4-3.582 4-8 4z',
    RESOLVE: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    NOTIFY: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9'
  }
  return icons[actionType] || 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2'
}

function formatTimestamp(timestamp) {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

async function fetchEvents() {
  loading.value = true
  try {
    const response = await fetch('/api/decisions?limit=100')
    const data = await response.json()
    if (data.data?.decisions) {
      events.value = data.data.decisions.map(d => ({
        id: d.id,
        timestamp: d.created_at,
        region_id: d.region_id,
        severity: d.decision_type === 'AUTO_ACT' ? 'HIGH' : 'MEDIUM',
        action_type: d.decision_type,
        summary: d.input_events?.summary || `Decision: ${d.decision_type}`,
        confidence: d.confidence
      }))
    }
  } catch (err) {
    console.error('Failed to fetch events:', err)
  } finally {
    loading.value = false
  }
}

function handleSSEEvent(data) {
  if (data.event_type === 'agent_assessment') {
    events.value.unshift({
      id: Date.now().toString(),
      timestamp: data.timestamp || new Date().toISOString(),
      region_id: data.region_id,
      severity: data.data?.severity || 'MEDIUM',
      action_type: data.data?.action_type || 'ALERT',
      summary: data.data?.summary || 'New agent assessment',
      confidence: data.data?.confidence
    })
    if (events.value.length > 100) {
      events.value.pop()
    }
  }
}

onMounted(() => {
  fetchEvents()
  agentStore.connectToSSE()
})

onUnmounted(() => {
  agentStore.disconnectSSE()
})
</script>

<template>
  <div class="event-feed" :style="{ maxHeight }">
    <div class="feed-header glass">
      <h2>Event Feed</h2>
      <div class="feed-filters">
        <select v-model="filterRegion" class="filter-select">
          <option value="">All Regions</option>
          <option v-for="region in regions" :key="region" :value="region">{{ region }}</option>
        </select>
        <select v-model="filterSeverity" class="filter-select">
          <option value="">All Severities</option>
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
          <option value="CRITICAL">Critical</option>
        </select>
        <select v-model="filterAction" class="filter-select">
          <option value="">All Actions</option>
          <option value="ALERT">Alert</option>
          <option value="REROUTE">Reroute</option>
          <option value="ESCALATE">Escalate</option>
          <option value="NOTIFY">Notify</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="loading__spinner"></div>
    </div>

    <div v-else-if="filteredEvents.length === 0" class="empty-state">
      <p class="empty-state__text">No events match your filters</p>
    </div>

    <div v-else class="feed-list">
      <div
        v-for="event in filteredEvents"
        :key="event.id"
        class="feed-item"
        :class="['risk-' + (event.severity || 'low').toLowerCase()]"
      >
        <div class="feed-item__icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path :d="getActionIcon(event.action_type)" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="feed-item__content">
          <div class="feed-item__header">
            <span class="feed-item__region">{{ event.region_id }}</span>
            <span :class="['badge', getSeverityClass(event.severity)]">
              {{ event.severity }}
            </span>
          </div>
          <p class="feed-item__summary">{{ event.summary }}</p>
          <div class="feed-item__meta">
            <span class="feed-item__time text-mono">{{ formatTimestamp(event.timestamp) }}</span>
            <span v-if="event.confidence" class="feed-item__confidence text-mono">
              {{ (event.confidence * 100).toFixed(0) }}% confidence
            </span>
          </div>
        </div>
        <div class="feed-item__indicator"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.event-feed {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.feed-header h2 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
}

.feed-filters {
  display: flex;
  gap: var(--spacing-2);
}

.filter-select {
  padding: var(--spacing-1) var(--spacing-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-bg-secondary);
  color: var(--color-text);
  font-size: var(--text-sm);
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-border-focus);
}

.feed-list {
  flex: 1;
  overflow-y: auto;
}

.feed-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  padding-left: calc(var(--spacing-4) + 3px);
  border-bottom: 1px solid var(--color-border);
  position: relative;
  transition: background-color var(--transition-fast);
}

.feed-item:hover {
  background-color: var(--color-bg-tertiary);
}

.feed-item:last-child {
  border-bottom: none;
}

.feed-item__icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background-color: var(--color-bg-tertiary);
  flex-shrink: 0;
  color: var(--color-text-secondary);
}

.feed-item__content {
  flex: 1;
  min-width: 0;
}

.feed-item__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-1);
}

.feed-item__region {
  font-weight: 600;
  font-size: var(--text-sm);
}

.feed-item__summary {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text);
  line-height: var(--leading-relaxed);
}

.feed-item__meta {
  display: flex;
  gap: var(--spacing-3);
  margin-top: var(--spacing-1);
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.feed-item__indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
}

.feed-item.risk-low .feed-item__indicator { background-color: var(--color-low); }
.feed-item.risk-medium .feed-item__indicator { background-color: var(--color-medium); }
.feed-item.risk-high .feed-item__indicator { background-color: var(--color-high); }
.feed-item.risk-critical .feed-item__indicator { background-color: var(--color-critical); }
</style>
