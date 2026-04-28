<script setup>
/**
 * SeverityTrend.vue
 * Row of colored dots showing severity history
 * Uses LOW/MEDIUM/HIGH/CRITICAL colors from design system
 */

const props = defineProps({
  history: {
    type: Array,
    default: () => [] // Array of severity strings: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
  },
  maxDots: {
    type: Number,
    default: 7
  },
  dotSize: {
    type: String,
    default: '10px'
  },
  showLabels: {
    type: Boolean,
    default: false
  }
})

const normalizedHistory = computed(() => {
  const validSeverities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
  const filtered = (props.history || [])
    .filter(s => s && validSeverities.includes(s.toUpperCase()))
    .map(s => s.toUpperCase())

  // Limit to maxDots
  const sliced = filtered.slice(-props.maxDots)

  // Pad with nulls if less than maxDots
  while (sliced.length < props.maxDots) {
    sliced.unshift(null)
  }

  return sliced
})

function getSeverityClass(severity) {
  if (!severity) return 'dot--empty'
  return `dot--${severity.toLowerCase()}`
}

function getSeverityLabel(severity, index) {
  if (!severity) return `No data`
  return `${severity} (${index + 1})`
}
</script>

<script>
import { computed } from 'vue'
</script>

<template>
  <div class="severity-trend">
    <div class="severity-dots" role="img" :aria-label="`Severity trend: ${normalizedHistory.filter(s => s).join(', ') || 'No data'}`">
      <div
        v-for="(severity, index) in normalizedHistory"
        :key="index"
        :class="['dot', getSeverityClass(severity)]"
        :style="{ width: dotSize, height: dotSize }"
        :title="getSeverityLabel(severity, index)"
      >
        <span v-if="!severity" class="dot-empty-indicator"></span>
      </div>
    </div>
    <div v-if="showLabels" class="severity-labels">
      <span class="severity-index">{{ normalizedHistory.filter(s => s).length }} readings</span>
    </div>
  </div>
</template>

<style scoped>
.severity-trend {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.severity-dots {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.dot {
  border-radius: var(--radius-full);
  flex-shrink: 0;
  position: relative;
  transition: transform var(--transition-fast);
}

.dot:hover {
  transform: scale(1.2);
}

/* Severity Colors */
.dot--empty {
  background-color: var(--color-bg-tertiary);
  border: 1px dashed var(--color-border);
}

.dot-empty-indicator {
  display: none;
}

.dot--low {
  background-color: var(--color-low);
  box-shadow: 0 0 6px var(--color-low-glow);
}

.dot--medium {
  background-color: var(--color-medium);
  box-shadow: 0 0 6px var(--color-medium-glow);
}

.dot--high {
  background-color: var(--color-high);
  box-shadow: 0 0 6px var(--color-high-glow);
}

.dot--critical {
  background-color: var(--color-critical);
  box-shadow: 0 0 8px var(--color-critical-glow);
  animation: pulse-critical-dot 2s infinite;
}

@keyframes pulse-critical-dot {
  0%, 100% {
    box-shadow: 0 0 6px var(--color-critical-glow);
  }
  50% {
    box-shadow: 0 0 12px var(--color-critical-glow);
  }
}

.severity-labels {
  display: flex;
  justify-content: flex-start;
}

.severity-index {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}
</style>
