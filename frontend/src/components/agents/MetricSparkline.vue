<script setup>
/**
 * MetricSparkline.vue
 * Horizontal bar showing value as percentage of max
 * Pure CSS, no external chart libraries
 */

const props = defineProps({
  value: {
    type: Number,
    default: null
  },
  max: {
    type: Number,
    default: 100
  },
  height: {
    type: String,
    default: '8px'
  },
  showLabel: {
    type: Boolean,
    default: false
  },
  label: {
    type: String,
    default: ''
  },
  color: {
    type: String,
    default: 'primary' // primary, low, medium, high, critical
  }
})

const percentage = computed(() => {
  if (props.value == null || props.max == null || props.max <= 0) {
    return 0
  }
  return Math.min(100, Math.max(0, (props.value / props.max) * 100))
})

const colorVar = computed(() => {
  const colorMap = {
    primary: 'var(--color-primary)',
    low: 'var(--color-low)',
    medium: 'var(--color-medium)',
    high: 'var(--color-high)',
    critical: 'var(--color-critical)'
  }
  return colorMap[props.color] || colorMap.primary
})
</script>

<script>
import { computed } from 'vue'
</script>

<template>
  <div class="metric-sparkline">
    <div v-if="showLabel && label" class="sparkline-label">
      {{ label }}
    </div>
    <div
      class="sparkline-bar"
      :style="{ height: height }"
      role="progressbar"
      :aria-valuenow="value"
      :aria-valuemin="0"
      :aria-valuemax="max"
    >
      <div
        class="sparkline-fill"
        :style="{
          width: percentage + '%',
          backgroundColor: colorVar
        }"
      ></div>
    </div>
    <div v-if="showLabel" class="sparkline-value">
      {{ value != null ? value : '—' }}
    </div>
  </div>
</template>

<style scoped>
.metric-sparkline {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  width: 100%;
}

.sparkline-label {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  min-width: 60px;
}

.sparkline-bar {
  flex: 1;
  background-color: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  position: relative;
}

.sparkline-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--transition-normal);
  min-width: 2px;
}

.sparkline-value {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text);
  min-width: 36px;
  text-align: right;
}
</style>
