<script setup>
/**
 * ConfidenceGauge.vue
 * Semicircular CSS gauge showing 0-100%
 * Pure CSS, no external chart libraries
 */

const props = defineProps({
  value: {
    type: Number,
    default: null
  },
  size: {
    type: String,
    default: '80px'
  },
  strokeWidth: {
    type: String,
    default: '8px'
  },
  showValue: {
    type: Boolean,
    default: true
  },
  label: {
    type: String,
    default: 'Confidence'
  }
})

const percentage = computed(() => {
  if (props.value == null || isNaN(props.value)) {
    return 0
  }
  return Math.min(100, Math.max(0, props.value))
})

// Conic gradient goes from 0% to percentage
// We need to map 0-100% to -135deg to 135deg (semicircle)
const rotation = computed(() => {
  // 0% = -135deg, 100% = 135deg
  return -135 + (percentage.value * 2.7)
})

const gaugeColor = computed(() => {
  if (percentage.value >= 80) return 'var(--color-low)'
  if (percentage.value >= 60) return 'var(--color-primary)'
  if (percentage.value >= 40) return 'var(--color-medium)'
  if (percentage.value >= 20) return 'var(--color-high)'
  return 'var(--color-critical)'
})

const formattedValue = computed(() => {
  if (props.value == null || isNaN(props.value)) return '—'
  return percentage.value.toFixed(0) + '%'
})
</script>

<script>
import { computed } from 'vue'
</script>

<template>
  <div class="confidence-gauge">
    <div
      class="gauge-container"
      :style="{ width: size, height: parseInt(size) / 2 + 'px' }"
      role="progressbar"
      :aria-valuenow="value"
      :aria-valuemin="0"
      :aria-valuemax="100"
      :aria-label="`${label}: ${formattedValue}`"
    >
      <!-- Background semicircle -->
      <div
        class="gauge-bg"
        :style="{
          borderWidth: strokeWidth
        }"
      ></div>

      <!-- Foreground semicircle (filled) -->
      <div
        v-if="percentage > 0"
        class="gauge-fill"
        :style="{
          borderWidth: strokeWidth,
          borderColor: gaugeColor,
          transform: `rotate(${rotation}deg)`
        }"
      ></div>

      <!-- Center dot -->
      <div class="gauge-center"></div>
    </div>

    <div v-if="showValue || label" class="gauge-info">
      <span v-if="showValue" class="gauge-value">{{ formattedValue }}</span>
      <span v-if="label" class="gauge-label">{{ label }}</span>
    </div>
  </div>
</template>

<style scoped>
.confidence-gauge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-2);
}

.gauge-container {
  position: relative;
  overflow: hidden;
}

.gauge-bg,
.gauge-fill {
  position: absolute;
  width: 100%;
  height: 200%;
  border-radius: 50%;
  border-style: solid;
  border-color: var(--color-bg-tertiary);
  box-sizing: border-box;
}

.gauge-bg {
  top: 0;
  left: 0;
  border-width: 8px;
}

.gauge-fill {
  top: 0;
  left: 0;
  border-width: 8px;
  border-color: var(--color-primary);
  clip-path: polygon(0 0, 100% 0, 100% 50%, 0 50%);
  transform-origin: center bottom;
  transition: transform var(--transition-slow), border-color var(--transition-normal);
}

.gauge-center {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 8px;
  height: 8px;
  background-color: var(--color-surface);
  border-radius: var(--radius-full);
  border: 2px solid var(--color-border);
}

.gauge-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.gauge-value {
  font-size: var(--text-lg);
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--color-text);
  line-height: 1;
}

.gauge-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
</style>
