<script setup>
import { computed } from 'vue'

const props = defineProps({
  reasoning: {
    type: String,
    default: ''
  },
  confidence: {
    type: Number,
    default: null
  },
  recommendation: {
    type: String,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const confidencePercent = computed(() => {
  if (props.confidence === null) return null
  return Math.round(props.confidence * 100)
})

const confidenceClass = computed(() => {
  if (props.confidence === null) return ''
  if (props.confidence >= 0.8) return 'high'
  if (props.confidence >= 0.5) return 'medium'
  return 'low'
})

const recommendationClass = computed(() => {
  if (!props.recommendation) return ''
  return `recommendation--${props.recommendation}`
})

const lines = computed(() => {
  if (!props.reasoning) return []
  return props.reasoning.split('\n').filter(line => line.trim())
})
</script>

<template>
  <div class="reasoning-terminal">
    <div class="terminal-header">
      <div class="terminal-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="4 17 10 11 4 5"/>
          <line x1="12" y1="19" x2="20" y2="19"/>
        </svg>
        <span>LLM Reasoning</span>
      </div>
      <div v-if="recommendation" class="terminal-badge" :class="recommendationClass">
        {{ recommendation.toUpperCase() }}
      </div>
    </div>

    <div v-if="loading" class="terminal-loading">
      <div class="loading-spinner"></div>
      <span>Analyzing routes...</span>
    </div>

    <div v-else-if="!reasoning" class="terminal-empty">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 16v-4M12 8h.01"/>
      </svg>
      <span>Run analysis to see reasoning</span>
    </div>

    <div v-else class="terminal-body">
      <div class="reasoning-lines">
        <div v-for="(line, i) in lines" :key="i" class="reasoning-line" :class="{ 'is-header': line.startsWith('#') || line.startsWith('##') }">
          {{ line }}
        </div>
      </div>

      <div v-if="confidencePercent !== null" class="confidence-section">
        <div class="confidence-label">Confidence Score</div>
        <div class="confidence-bar">
          <div class="confidence-fill" :class="confidenceClass" :style="{ width: `${confidencePercent}%` }"></div>
        </div>
        <div class="confidence-value" :class="confidenceClass">{{ confidencePercent }}%</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reasoning-terminal {
  background: #0f172a;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  overflow: hidden;
}

.terminal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
  background: rgba(15, 22, 35, 0.95);
}

.terminal-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  color: var(--color-primary-light);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.terminal-badge {
  font-size: var(--text-xs);
  font-weight: 600;
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.terminal-badge.recommendation--accept {
  background: var(--color-low-bg);
  color: var(--color-low);
}

.terminal-badge.recommendation--reject {
  background: var(--color-critical-bg);
  color: var(--color-critical);
}

.terminal-badge.recommendation--review {
  background: var(--color-high-bg);
  color: var(--color-high);
}

.terminal-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-3);
  padding: var(--spacing-8);
  color: var(--color-text-secondary);
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.terminal-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-8);
  color: var(--color-text-tertiary);
  font-family: var(--font-sans);
}

.terminal-body {
  padding: var(--spacing-4);
  max-height: 400px;
  overflow-y: auto;
}

.reasoning-lines {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.reasoning-line {
  color: var(--color-text-secondary);
  line-height: 1.6;
  padding: var(--spacing-1) 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.reasoning-line:last-child {
  border-bottom: none;
}

.reasoning-line.is-header {
  color: var(--color-primary-light);
  font-weight: 600;
  margin-top: var(--spacing-2);
}

.confidence-section {
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border);
}

.confidence-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--spacing-2);
}

.confidence-bar {
  height: 6px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--spacing-1);
}

.confidence-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.5s ease;
}

.confidence-fill.high {
  background: var(--color-low);
}

.confidence-fill.medium {
  background: var(--color-high);
}

.confidence-fill.low {
  background: var(--color-critical);
}

.confidence-value {
  font-size: var(--text-xs);
  font-weight: 600;
}

.confidence-value.high {
  color: var(--color-low);
}

.confidence-value.medium {
  color: var(--color-high);
}

.confidence-value.low {
  color: var(--color-critical);
}
</style>