<script setup>
import { computed } from 'vue'
import { formatCurrency } from '@/utils/metrics.js'

const props = defineProps({
  scenarios: {
    type: Array,
    default: () => []
  }
})

// Total scenarios count
const totalScenarios = computed(() => props.scenarios.length)

// Average cascade depth - computed from scenarios data
// Each scenario may have affected_regions count as a proxy for cascade depth
const averageCascadeDepth = computed(() => {
  if (!props.scenarios.length) return 0
  const totalDepth = props.scenarios.reduce((sum, s) => {
    // Use affected_regions length as cascade depth proxy, default to 1
    return sum + (s.affected_regions?.length || 1)
  }, 0)
  return (totalDepth / props.scenarios.length).toFixed(1)
})

// Total estimated financial impact - sum of all scenario impacts
const totalFinancialImpact = computed(() => {
  return props.scenarios.reduce((sum, s) => {
    return sum + (s.financial_impact_usd || 0)
  }, 0)
})

// Most common category - computed from scenarios
const mostCommonCategory = computed(() => {
  if (!props.scenarios.length) return 'N/A'
  const categoryCounts = {}
  props.scenarios.forEach(s => {
    const cat = s.category || 'UNKNOWN'
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1
  })
  const sorted = Object.entries(categoryCounts).sort((a, b) => b[1] - a[1])
  return sorted[0]?.[0] || 'N/A'
})

// Most severe scenario - highest severity
const mostSevereScenario = computed(() => {
  if (!props.scenarios.length) return { name: 'N/A', severity: 'LOW' }
  const severityOrder = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 }
  const sorted = [...props.scenarios].sort((a, b) => {
    const sevA = severityOrder[a.severity?.toUpperCase()] || 0
    const sevB = severityOrder[b.severity?.toUpperCase()] || 0
    return sevB - sevA
  })
  return sorted[0] || { name: 'N/A', severity: 'LOW' }
})

// Format category for display
function formatCategoryLabel(category) {
  if (!category || category === 'N/A') return 'N/A'
  return category.charAt(0) + category.slice(1).toLowerCase()
}

// Icon SVG paths for each metric
const icons = {
  scenarios: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
  cascade: 'M13 10V3L4 14h7v7l9-11h-7z',
  financial: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1.41 16.09V20h-2.67v-1.93c-1.71-.36-3.16-1.46-3.27-3.4h1.96c.1 1.05.82 1.87 2.65 1.87 1.96 0 2.4-.98 2.4-1.59 0-.83-.44-1.61-2.67-2.14-2.48-.6-4.18-1.62-4.18-3.67 0-1.72 1.39-2.84 3.11-3.21V4h2.67v1.93c1.38.36 2.4 1.7 2.4 3.41 0 2.31-1.91 3.46-4.7 3.46-1.68 0-2.74-.81-2.74-2.05 0-1.16.88-1.78 2.76-2.29 2.07-.54 3.8-1.17 3.8-3.28 0-1.44-1.04-2.68-2.77-3.01V2h-2.67v1.93c-1.53.38-2.68 1.74-2.68 3.28 0 1.73 1.31 2.87 3.57 2.87 1.57 0 2.78-.79 2.78-2.02 0-.95-.58-1.64-2.44-2.24-1.84-.59-3.86-1.24-3.86-3.24 0-1.36 1.11-2.52 2.73-2.83V.17h2.67v1.88c1.43.31 2.45 1.58 2.45 3.07 0 1.61-1.31 2.88-3.4 2.88-1.46 0-2.59-.74-2.59-2 0-.95.68-1.67 2.53-2.17 1.94-.53 3.67-1.15 3.67-3.22 0-1.37-1.11-2.5-2.86-2.76V0h-2.67v1.91c-1.59.33-2.73 1.7-2.73 3.29 0 1.79 1.46 3.07 3.52 3.07 1.61 0 2.9-.89 2.9-2.38 0-.96-.61-1.76-2.31-2.22-1.78-.48-4.08-1.06-4.08-3.07 0-1.62 1.35-2.94 3.1-3.1V-.02h2.67v1.88c-1.51.16-2.65 1.51-2.65 3.02 0 1.81 1.46 3.08 3.4 3.08 1.52 0 2.77-.84 2.77-2.24 0-.91-.64-1.68-2.44-2.17-1.9-.52-4.14-1.14-4.14-3.17 0-1.66 1.4-3.02 3.2-3.27V-1.5h2.67v1.92c-1.46.25-2.51 1.64-2.51 3.26 0 1.76 1.42 2.99 3.35 2.99 1.48 0 2.68-.79 2.68-2.12 0-.98-.63-1.77-2.44-2.27-1.88-.52-4.06-1.16-4.06-3.16 0-1.61 1.35-2.92 3.11-3.17V-1.7h2.67v1.93c-1.44.25-2.47 1.58-2.47 3.18 0 1.79 1.46 3.04 3.52 3.04 1.45 0 2.63-.76 2.63-2.03 0-.92-.59-1.69-2.4-2.18-1.87-.51-4.02-1.12-4.02-3.12 0-1.56 1.3-2.83 2.99-3.07V-2h2.67v1.85c-1.38.24-2.37 1.51-2.37 3.02 0 1.72 1.39 2.93 3.29 2.93 1.39 0 2.52-.71 2.52-1.92 0-.89-.54-1.62-2.35-2.1-1.82-.49-3.94-1.09-3.94-3.04 0-1.5 1.25-2.72 2.87-2.96V-2.4h2.67v1.82c-1.33.23-2.28 1.43-2.28 2.89 0 1.66 1.34 2.83 3.15 2.83 1.33 0 2.41-.69 2.41-1.84 0-.86-.5-1.57-2.27-2.04-1.75-.47-3.77-1.05-3.77-2.94 0-1.43 1.19-2.6 2.74-2.82V-2.6h2.67v1.8c-1.26.22-2.16 1.36-2.16 2.74 0 1.59 1.28 2.71 3.02 2.71 1.27 0 2.3-.66 2.3-1.75 0-.82-.48-1.5-2.19-1.96-1.67-.45-3.6-1.01-3.6-2.82 0-1.36 1.13-2.47 2.61-2.68V-2.8h2.67v1.76c-1.18.21-2.02 1.28-2.02 2.57 0 1.51 1.22 2.57 2.87 2.57 1.2 0 2.18-.63 2.18-1.66 0-.78-.45-1.43-2.1-1.88-1.59-.43-3.43-.96-3.43-2.69 0-1.28 1.07-2.33 2.47-2.53V-3h2.67v1.73c-1.1.19-1.89 1.2-1.89 2.4 0 1.42 1.15 2.42 2.71 2.42 1.13 0 2.05-.59 2.05-1.57 0-.73-.43-1.35-2-1.77-1.5-.4-3.25-.9-3.25-2.55 0-1.2 1-2.18 2.32-2.36V-3.2h2.67v1.69c-1.02.18-1.75 1.11-1.75 2.22 0 1.33 1.08 2.26 2.54 2.26 1.05 0 1.91-.55 1.91-1.46 0-.68-.4-1.26-1.91-1.65-1.41-.36-3.04-.84-3.04-2.41 0-1.11.93-2.02 2.15-2.19V-3.4h2.67v1.64c-.93.16-1.59 1.02-1.59 2.02 0 1.23.99 2.1 2.36 2.1.97 0 1.76-.51 1.76-1.36 0-.62-.37-1.15-1.79-1.52-1.31-.33-2.82-.74-2.82-2.24 0-1.01.84-1.84 1.94-1.99V-3.6h2.67v1.59c-.84.14-1.44.92-1.44 1.82 0 1.13.9 1.92 2.16 1.92.88 0 1.6-.46 1.6-1.24 0-.56-.33-1.03-1.66-1.38-1.21-.3-2.6-.68-2.6-2.06 0-.92.77-1.67 1.77-1.81V-3.8h2.67v1.53c-.74.12-1.27.81-1.27 1.6 0 1.02.8 1.74 1.95 1.74.78 0 1.42-.41 1.42-1.11 0-.5-.29-.92-1.5-1.23-1.1-.27-2.38-.61-2.38-1.87 0-.82.68-1.49 1.57-1.61V-4h2.67v1.46c-.64.1-1.1.7-1.1 1.37 0 .91.7 1.55 1.73 1.55.68 0 1.24-.36 1.24-.98 0-.43-.26-.79-1.33-1.08-.98-.24-2.11-.54-2.11-1.67 0-.71.59-1.29 1.36-1.39V-4.2h2.67v1.38c-.53.08-.91.58-.91 1.14 0 .79.58 1.35 1.49 1.35.57 0 1.04-.3 1.04-.85 0-.36-.22-.66-1.14-.92-.84-.2-1.81-.45-1.81-1.44 0-.6.5-1.08 1.14-1.17V-4.4h2.67v1.28c-.41.06-.7.46-.7.89 0 .66.46 1.13 1.23 1.13.46 0 .84-.24.84-.7 0-.29-.18-.53-.95-.75-.69-.16-1.49-.36-1.49-1.19 0-.48.4-.86.92-.93V-4.6h2.67v1.18c-.29.04-.5.32-.5.63 0 .53.37.9.98.9.36 0 .65-.19.65-.56 0-.23-.14-.42-.75-.59-.53-.12-1.15-.28-1.15-.96 0-.36.3-.65.7-.7V-4.8h2.67v1.05c-.18.02-.31.18-.31.36 0 .4.28.68.75.68.27 0 .49-.14.49-.42 0-.17-.11-.32-.56-.44-.4-.09-.87-.2-.87-.72 0-.24.2-.44.5-.47V-5h-2.67z',
  category: 'M4 6h16M4 10h16M4 14h16M4 18h16',
  severity: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.5-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
}
</script>

<template>
  <div class="metrics-summary">
    <div class="metrics-grid">
      <!-- Total Scenarios -->
      <div class="metric-card">
        <div class="metric-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path :d="icons.scenarios" />
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-value">{{ totalScenarios }}</span>
          <span class="metric-label">Total Scenarios</span>
        </div>
      </div>

      <!-- Average Cascade Depth -->
      <div class="metric-card">
        <div class="metric-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path :d="icons.cascade" />
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-value">{{ averageCascadeDepth }}</span>
          <span class="metric-label">Avg Cascade Depth</span>
        </div>
      </div>

      <!-- Total Financial Impact -->
      <div class="metric-card metric-card--highlight">
        <div class="metric-icon metric-icon--financial">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path :d="icons.financial" />
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-value">{{ formatCurrency(totalFinancialImpact) }}</span>
          <span class="metric-label">Total Impact</span>
        </div>
      </div>

      <!-- Most Common Category -->
      <div class="metric-card">
        <div class="metric-icon metric-icon--category">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path :d="icons.category" />
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-value">{{ formatCategoryLabel(mostCommonCategory) }}</span>
          <span class="metric-label">Top Category</span>
        </div>
      </div>

      <!-- Most Severe Scenario -->
      <div class="metric-card">
        <div class="metric-icon metric-icon--severity" :class="`metric-icon--${(mostSevereScenario.severity || 'low').toLowerCase()}`">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path :d="icons.severity" />
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-value metric-value--severity" :class="`severity--${(mostSevereScenario.severity || 'low').toLowerCase()}`">
            {{ mostSevereScenario.name || 'N/A' }}
          </span>
          <span class="metric-label">Most Severe</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.metrics-summary {
  width: 100%;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--spacing-4);
}

/* Stat Card */
.metric-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: all var(--transition-normal);
}

.metric-card:hover {
  border-color: var(--color-border-hover);
  box-shadow: var(--shadow-md);
}

.metric-card--highlight {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(99, 102, 241, 0.04) 100%);
  border-color: rgba(59, 130, 246, 0.3);
}

/* Icon Container */
.metric-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.metric-icon svg {
  width: 20px;
  height: 20px;
  color: var(--color-primary-light);
}

.metric-icon--financial svg {
  color: var(--color-success);
}

.metric-icon--category svg {
  color: var(--color-secondary);
}

.metric-icon--severity svg {
  color: var(--color-high);
}

.metric-icon--critical svg {
  color: var(--color-critical);
}

/* Content */
.metric-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  min-width: 0;
}

.metric-value {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-value--severity {
  font-size: var(--text-sm);
  font-weight: 600;
}

.metric-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 500;
}

/* Severity Colors */
.severity--low { color: var(--color-low); }
.severity--medium { color: var(--color-medium); }
.severity--high { color: var(--color-high); }
.severity--critical { color: var(--color-critical); }

/* Responsive */
@media (max-width: 1200px) {
  .metrics-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-3);
  }

  .metric-card {
    padding: var(--spacing-3);
    flex-direction: column;
    text-align: center;
    gap: var(--spacing-2);
  }

  .metric-icon {
    width: 36px;
    height: 36px;
  }

  .metric-icon svg {
    width: 18px;
    height: 18px;
  }

  .metric-value {
    font-size: var(--text-base);
  }
}

@media (max-width: 480px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .metric-card {
    flex-direction: row;
    text-align: left;
  }
}
</style>