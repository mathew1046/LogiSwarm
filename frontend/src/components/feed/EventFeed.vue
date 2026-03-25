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

const severityColors = {
  LOW: 'var(--color-low)',
  MEDIUM: 'var(--color-medium)',
  HIGH: 'var(--color-high)',
  CRITICAL: 'var(--color-critical)'
}

function getSeverityColor(severity) {
  return severityColors[severity?.toUpperCase()] || severityColors.LOW
}

function getActionIcon(actionType) {
  const icons = {
    ALERT: '⚠️',
    REROUTE: '🔀',
    ESCALATE: '📈',
    RESOLVE: '✓',
    NOTIFY: '📧'
  }
  return icons[actionType] || '📋'
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
    <div class="feed-header">
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
      <p>No events match your filters</p>
    </div>

    <div v-else class="feed-list">
      <div 
        v-for="event in filteredEvents" 
        :key="event.id" 
        class="feed-item"
        :class="'severity-' + (event.severity || 'low').toLowerCase()"
      >
        <div class="feed-item__icon">
          {{ getActionIcon(event.action_type) }}
        </div>
        <div class="feed-item__content">
          <div class="feed-item__header">
            <span class="feed-item__region">{{ event.region_id }}</span>
            <span 
              class="feed-item__severity"
              :style="{ backgroundColor: getSeverityColor(event.severity) }"
            >
              {{ event.severity }}
            </span>
          </div>
          <p class="feed-item__summary">{{ event.summary }}</p>
          <div class="feed-item__meta">
            <span class="feed-item__time">{{ formatTimestamp(event.timestamp) }}</span>
            <span v-if="event.confidence" class="feed-item__confidence">
              {{ (event.confidence * 100).toFixed(0) }}% confidence
            </span>
          </div>
        </div>
        <div class="feed-item__indicator" :style="{ backgroundColor: getSeverityColor(event.severity) }"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.event-feed {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
  background-color: var(--color-surface);
  position: sticky;
  top: 0;
  z-index: 10;
}

.feed-header h2 {
  margin: 0;
}

.feed-filters {
  display: flex;
  gap: var(--spacing-2);
}

.filter-select {
  padding: var(--spacing-1) var(--spacing-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-bg);
  color: var(--color-text);
  font-size: var(--text-sm);
}

.feed-list {
  flex: 1;
  overflow-y: auto;
}

.feed-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border-bottom: 1px solid var(--color-border);
  position: relative;
  transition: background-color var(--transition-fast);
}

.feed-item:hover {
  background-color: var(--color-bg-secondary);
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
  background-color: var(--color-bg-secondary);
  flex-shrink: 0;
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

.feed-item__severity {
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 500;
  color: white;
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
  color: var(--color-text-secondary);
}

.feed-item__indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
}

.severity-low .feed-item__indicator { background-color: var(--color-low); }
.severity-medium .feed-item__indicator { background-color: var(--color-medium); }
.severity-high .feed-item__indicator { background-color: var(--color-high); }
.severity-critical .feed-item__indicator { background-color: var(--color-critical); }
</style>