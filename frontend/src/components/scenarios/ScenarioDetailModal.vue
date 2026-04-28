<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { formatCurrency } from '@/utils/metrics.js'

const props = defineProps({
  scenario: {
    type: Object,
    required: true
  },
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'run-simulation'])

const severityClass = computed(() => `badge--${(props.scenario.severity || 'low').toLowerCase()}`)

const categoryColors = {
  CANAL: 'var(--color-category-canal)',
  PORT: 'var(--color-category-port)',
  WEATHER: 'var(--color-category-weather)',
  GEOPOLITICAL: 'var(--color-category-geopolitical)',
  CYBER: 'var(--color-category-cyber)',
  LABOR: 'var(--color-category-labor)',
  PANDEMIC: 'var(--color-category-pandemic)',
  INFRASTRUCTURE: 'var(--color-category-infrastructure)'
}

const categoryColor = computed(() => categoryColors[props.scenario.category] || categoryColors.INFRASTRUCTURE)

const dateRange = computed(() => {
  if (!props.scenario.date_start && !props.scenario.date_end) return 'Date range unknown'
  const start = props.scenario.date_start || 'Unknown'
  const end = props.scenario.date_end || 'Unknown'
  return `${start} — ${end}`
})

const durationDisplay = computed(() => {
  if (!props.scenario.duration_days) return null
  return `${props.scenario.duration_days} day${props.scenario.duration_days !== 1 ? 's' : ''}`
})

const timelineStyle = computed(() => {
  const start = new Date(props.scenario.date_start || '2024-01-01').getTime()
  const end = new Date(props.scenario.date_end || '2024-12-31').getTime()
  const now = Date.now()
  const total = end - start
  const current = now - start
  const pct = Math.min(Math.max((current / total) * 100, 0), 100)
  return { left: '0%', width: `${pct}%` }
})

function handleBackdropClick(e) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}

function handleKeydown(e) {
  if (e.key === 'Escape' && props.visible) {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible"
        class="modal-backdrop"
        @click="handleBackdropClick"
      >
        <div class="modal-container" role="dialog" aria-modal="true" :aria-labelledby="scenario.name">
          <!-- Header -->
          <div class="modal-header">
            <div class="header-content">
              <div class="header-top">
                <span
                  class="category-dot"
                  :style="{ background: categoryColor }"
                ></span>
                <span class="category-label">{{ scenario.category }}</span>
              </div>
              <h2 class="scenario-name">{{ scenario.name }}</h2>
              <div class="date-range">{{ dateRange }}</div>
            </div>
            <button class="close-btn" @click="$emit('close')" aria-label="Close modal">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>

          <!-- Timeline -->
          <div v-if="scenario.date_start || scenario.date_end" class="timeline-section">
            <div class="timeline-label">
              <span>Timeline</span>
              <span v-if="durationDisplay" class="duration-badge">{{ durationDisplay }}</span>
            </div>
            <div class="timeline-bar">
              <div class="timeline-track">
                <div class="timeline-fill" :style="{ background: categoryColor }"></div>
              </div>
              <div class="timeline-dates">
                <span>{{ scenario.date_start || 'Start' }}</span>
                <span>{{ scenario.date_end || 'End' }}</span>
              </div>
            </div>
          </div>

          <!-- Severity & Financial Impact -->
          <div class="metrics-row">
            <div class="metric-card">
              <span class="metric-label">Severity</span>
              <span class="badge" :class="severityClass">
                {{ (scenario.severity || 'LOW').toUpperCase() }}
              </span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Financial Impact</span>
              <span class="metric-value impact-value">{{ formatCurrency(scenario.financial_impact_usd) }}</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Trigger Region</span>
              <span class="metric-value region-value">{{ scenario.trigger_region || 'Unknown' }}</span>
            </div>
          </div>

          <!-- Description -->
          <div v-if="scenario.description" class="section">
            <h3 class="section-title">Description</h3>
            <p class="description-text">{{ scenario.description }}</p>
          </div>

          <!-- Affected Regions -->
          <div v-if="scenario.affected_regions?.length" class="section">
            <h3 class="section-title">Affected Regions</h3>
            <div class="regions-list">
              <button
                v-for="region in scenario.affected_regions"
                :key="region"
                class="region-tag"
                @click="$emit('close')"
              >
                {{ region }}
              </button>
            </div>
          </div>

          <!-- Cascade Effects -->
          <div v-if="scenario.cascade_effects?.length" class="section">
            <h3 class="section-title">Cascade Effects</h3>
            <ul class="effects-list">
              <li v-for="(effect, idx) in scenario.cascade_effects" :key="idx" class="effect-item">
                <span class="effect-bullet"></span>
                {{ effect }}
              </li>
            </ul>
          </div>

          <!-- Mitigation Strategies -->
          <div v-if="scenario.mitigation_strategies?.length" class="section">
            <h3 class="section-title">Mitigation Strategies</h3>
            <ul class="effects-list">
              <li v-for="(strategy, idx) in scenario.mitigation_strategies" :key="idx" class="effect-item mitigation-item">
                <span class="mitigation-icon">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 12l2 2 4-4M22 12c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2s10 4.477 10 10z" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </span>
                {{ strategy }}
              </li>
            </ul>
          </div>

          <!-- Sources -->
          <div v-if="scenario.sources?.length" class="section">
            <h3 class="section-title">Sources</h3>
            <div class="sources-list">
              <a
                v-for="(source, idx) in scenario.sources"
                :key="idx"
                :href="source"
                target="_blank"
                rel="noopener noreferrer"
                class="source-link"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ source }}
              </a>
            </div>
          </div>

          <!-- Footer Actions -->
          <div class="modal-footer">
            <button class="btn btn--secondary" @click="$emit('close')">
              Close
            </button>
            <button class="btn btn--primary" @click="$emit('run-simulation', scenario)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 3l14 9-14 9V3z" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Run Simulation
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--spacing-4);
}

.modal-container {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-xl);
}

/* Header */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--spacing-5);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
}

.header-content {
  flex: 1;
}

.header-top {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-2);
}

.category-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.category-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
}

.scenario-name {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 var(--spacing-1);
  line-height: var(--leading-tight);
}

.date-range {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.close-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text);
}

/* Timeline */
.timeline-section {
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--color-border);
}

.timeline-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-2);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.duration-badge {
  font-size: var(--text-xs);
  padding: 0.15rem 0.4rem;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  color: var(--color-text-tertiary);
  font-family: var(--font-mono);
}

.timeline-bar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.timeline-track {
  height: 6px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  position: relative;
}

.timeline-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  border-radius: var(--radius-full);
  opacity: 0.8;
}

.timeline-dates {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  font-family: var(--font-mono);
}

/* Metrics Row */
.metrics-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-3);
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--color-border);
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.metric-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-value {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}

.impact-value {
  font-family: var(--font-mono);
  color: var(--color-primary-light);
}

.region-value {
  text-transform: capitalize;
}

/* Sections */
.section {
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--color-border);
}

.section:last-of-type {
  border-bottom: none;
}

.section-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.description-text {
  font-size: var(--text-sm);
  color: var(--color-text);
  line-height: var(--leading-relaxed);
  margin: 0;
}

/* Regions */
.regions-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.region-tag {
  font-size: var(--text-xs);
  padding: var(--spacing-1) var(--spacing-3);
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.region-tag:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

/* Effects List */
.effects-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.effect-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  font-size: var(--text-sm);
  color: var(--color-text);
  line-height: var(--leading-normal);
}

.effect-bullet {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  flex-shrink: 0;
  margin-top: 0.4rem;
}

.mitigation-item .mitigation-icon {
  color: var(--color-success);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  margin-top: 0.1rem;
}

/* Sources */
.sources-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.source-link {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-xs);
  color: var(--color-primary-light);
  text-decoration: none;
  word-break: break-all;
  transition: color var(--transition-fast);
}

.source-link:hover {
  color: var(--color-primary);
}

/* Footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
  padding: var(--spacing-4) var(--spacing-5);
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
}

/* Modal Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: all 200ms ease;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: all 200ms ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95) translateY(10px);
}

/* Responsive */
@media (max-width: 640px) {
  .modal-backdrop {
    padding: var(--spacing-2);
    align-items: flex-end;
  }

  .modal-container {
    max-height: 85vh;
    border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  }

  .metrics-row {
    grid-template-columns: 1fr;
    gap: var(--spacing-3);
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .modal-footer .btn {
    width: 100%;
  }
}
</style>
