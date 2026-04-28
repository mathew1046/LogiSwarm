<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentRoute: {
    type: Object,
    default: null
  },
  proposedRoute: {
    type: Object,
    default: null
  },
  deltaCost: {
    type: Number,
    default: null
  },
  deltaTransitHours: {
    type: Number,
    default: null
  },
  deltaReliability: {
    type: Number,
    default: null
  }
})

const formatCost = (val) => {
  if (val === null || val === undefined) return '—'
  return `$${val.toFixed(2)}`
}

const formatHours = (val) => {
  if (val === null || val === undefined) return '—'
  if (val < 24) return `${Math.round(val)}h`
  const days = Math.floor(val / 24)
  const hours = Math.round(val % 24)
  return days > 0 ? `${days}d ${hours}h` : `${hours}h`
}

const formatPercent = (val) => {
  if (val === null || val === undefined) return '—'
  return `${(val * 100).toFixed(0)}%`
}

const costDeltaClass = computed(() => {
  if (props.deltaCost === null) return ''
  return props.deltaCost <= 0 ? 'delta--good' : 'delta--bad'
})

const transitDeltaClass = computed(() => {
  if (props.deltaTransitHours === null) return ''
  return props.deltaTransitHours <= 0 ? 'delta--good' : 'delta--bad'
})

const reliabilityDeltaClass = computed(() => {
  if (props.deltaReliability === null) return ''
  return props.deltaReliability >= 0 ? 'delta--good' : 'delta--bad'
})

const formatDelta = (val, unit = '') => {
  if (val === null || val === undefined) return '—'
  const sign = val > 0 ? '+' : ''
  return `${sign}${val.toFixed(1)}${unit}`
}
</script>

<template>
  <div class="comparison-card">
    <div class="card-header">
      <span class="card-label">Route Comparison</span>
    </div>

    <div v-if="!currentRoute || !proposedRoute" class="card-empty">
      <span>Select routes to compare</span>
    </div>

    <div v-else class="comparison-grid">
      <div class="route-column route-column--current">
        <div class="route-indicator current">
          <span class="route-dot"></span>
          Current
        </div>
        <div class="route-name">{{ currentRoute.name || currentRoute.id }}</div>
        <div class="route-stats">
          <div class="stat-row">
            <span class="stat-label">Cost</span>
            <span class="stat-value">{{ formatCost(currentRoute.cost) }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Transit</span>
            <span class="stat-value">{{ formatHours(currentRoute.transit_hours) }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Reliability</span>
            <span class="stat-value">{{ formatPercent(currentRoute.reliability) }}</span>
          </div>
        </div>
      </div>

      <div class="delta-column">
        <div class="delta-label">Delta</div>
        <div class="delta-items">
          <div class="delta-item" :class="costDeltaClass">
            <span class="delta-value">{{ formatDelta(deltaCost, '') }}</span>
            <span class="delta-sublabel">cost</span>
          </div>
          <div class="delta-item" :class="transitDeltaClass">
            <span class="delta-value">{{ formatDelta(deltaTransitHours, 'h') }}</span>
            <span class="delta-sublabel">time</span>
          </div>
          <div class="delta-item" :class="reliabilityDeltaClass">
            <span class="delta-value">{{ formatDelta(deltaReliability) }}</span>
            <span class="delta-sublabel">reliability</span>
          </div>
        </div>
      </div>

      <div class="route-column route-column--proposed">
        <div class="route-indicator proposed">
          <span class="route-dot"></span>
          Proposed
        </div>
        <div class="route-name">{{ proposedRoute.name || proposedRoute.id }}</div>
        <div class="route-stats">
          <div class="stat-row">
            <span class="stat-label">Cost</span>
            <span class="stat-value">{{ formatCost(proposedRoute.cost) }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Transit</span>
            <span class="stat-value">{{ formatHours(proposedRoute.transit_hours) }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Reliability</span>
            <span class="stat-value">{{ formatPercent(proposedRoute.reliability) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comparison-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.card-header {
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
}

.card-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-secondary);
}

.card-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-6);
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
}

.comparison-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 0;
}

.route-column {
  padding: var(--spacing-4);
}

.route-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--spacing-3);
}

.route-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.route-indicator.current {
  color: var(--color-critical);
}

.route-indicator.current .route-dot {
  background: var(--color-critical);
  box-shadow: 0 0 6px var(--color-critical-glow);
}

.route-indicator.proposed {
  color: var(--color-low);
}

.route-indicator.proposed .route-dot {
  background: var(--color-low);
  box-shadow: 0 0 6px var(--color-low-glow);
}

.route-name {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.route-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-2);
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.stat-value {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text);
  font-family: var(--font-mono);
}

.delta-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-4) var(--spacing-3);
  background: var(--color-bg-secondary);
  border-left: 1px solid var(--color-border);
  border-right: 1px solid var(--color-border);
  min-width: 80px;
}

.delta-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-3);
}

.delta-items {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.delta-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.delta-value {
  font-size: var(--text-sm);
  font-weight: 600;
  font-family: var(--font-mono);
}

.delta-sublabel {
  font-size: 10px;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.delta--good .delta-value {
  color: var(--color-low);
}

.delta--bad .delta-value {
  color: var(--color-critical);
}
</style>