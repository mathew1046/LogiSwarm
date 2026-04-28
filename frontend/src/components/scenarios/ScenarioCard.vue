<!--
LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
Copyright (C) 2025 LogiSwarm Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
-->

<script setup>
import { computed } from 'vue'
import { formatCurrency } from '@/utils/metrics'

const props = defineProps({
  scenario: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

const emit = defineEmits(['click', 'run-simulation'])

const severityClass = computed(() => {
  const s = (props.scenario.severity || 'low').toLowerCase()
  return `severity--${s}`
})

const severityColor = computed(() => {
  const colors = {
    low: 'var(--color-low)',
    medium: 'var(--color-medium)',
    high: 'var(--color-high)',
    critical: 'var(--color-critical)'
  }
  return colors[(props.scenario.severity || 'low').toLowerCase()] || colors.low
})

const categoryClass = computed(() => {
  const cat = (props.scenario.category || 'infrastructure').toLowerCase()
  return `category--${cat}`
})

const formattedImpact = computed(() => {
  return formatCurrency(props.scenario.financial_impact_usd)
})

const dateRange = computed(() => {
  const start = props.scenario.date_start
  const end = props.scenario.date_end
  if (!start && !end) return 'Date unavailable'
  if (!end) return start
  if (!start) return end
  return `${start} — ${end}`
})

const affectedRegionCount = computed(() => {
  const regions = props.scenario.affected_regions
  if (!regions || !Array.isArray(regions)) return 0
  return regions.length
})

const shortDescription = computed(() => {
  const desc = props.scenario.description
  if (!desc) return 'No description available'
  // Truncate to ~100 characters for card preview
  if (desc.length <= 100) return desc
  return desc.slice(0, 97) + '...'
})

function handleCardClick() {
  emit('click', props.scenario)
}

function handleRunSimulation(event) {
  event.stopPropagation()
  emit('run-simulation', props.scenario)
}
</script>

<template>
  <div
    class="scenario-card"
    :class="severityClass"
    @click="handleCardClick"
  >
    <div class="card-header">
      <div class="severity-indicator" :style="{ backgroundColor: severityColor }"></div>
      <span :class="['badge', 'severity-badge', severityClass]">
        {{ (scenario.severity || 'LOW').toUpperCase() }}
      </span>
      <span :class="['badge', 'category-badge', categoryClass]">
        {{ scenario.category || 'INFRASTRUCTURE' }}
      </span>
    </div>

    <h3 class="scenario-name">{{ scenario.name || 'Unnamed Scenario' }}</h3>

    <div class="date-range">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
        <line x1="16" y1="2" x2="16" y2="6"/>
        <line x1="8" y1="2" x2="8" y2="6"/>
        <line x1="3" y1="10" x2="21" y2="10"/>
      </svg>
      <span>{{ dateRange }}</span>
    </div>

    <p class="description">{{ shortDescription }}</p>

    <div class="metrics-row">
      <div class="metric">
        <span class="metric-label">Financial Impact</span>
        <span class="metric-value text-mono">{{ formattedImpact }}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Trigger Region</span>
        <span class="metric-value">{{ scenario.trigger_region || 'Unknown' }}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Affected Regions</span>
        <span class="metric-value text-mono">{{ affectedRegionCount }}</span>
      </div>
    </div>

    <button class="run-btn" @click="handleRunSimulation">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="5 3 19 12 5 21 5 3"/>
      </svg>
      Run Simulation
    </button>
  </div>
</template>

<style scoped>
.scenario-card {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.scenario-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  border-color: var(--color-primary-light);
}

.scenario-card:active {
  transform: translateY(0);
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.severity-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.severity--critical .severity-indicator {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: var(--text-xs);
  font-weight: 600;
  border-radius: var(--radius-full);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.severity-badge.severity--low {
  background: rgba(34, 197, 94, 0.15);
  color: var(--color-low);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.severity-badge.severity--medium {
  background: rgba(234, 179, 8, 0.15);
  color: var(--color-medium);
  border: 1px solid rgba(234, 179, 8, 0.3);
}

.severity-badge.severity--high {
  background: rgba(249, 115, 22, 0.15);
  color: var(--color-high);
  border: 1px solid rgba(249, 115, 22, 0.3);
}

.severity-badge.severity--critical {
  background: rgba(239, 68, 68, 0.15);
  color: var(--color-critical);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.category-badge {
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}

.category-badge.category--canal {
  background: rgba(59, 130, 246, 0.1);
  color: var(--color-category-canal);
  border-color: rgba(59, 130, 246, 0.3);
}

.category-badge.category--port {
  background: rgba(168, 85, 247, 0.1);
  color: var(--color-category-port);
  border-color: rgba(168, 85, 247, 0.3);
}

.category-badge.category--weather {
  background: rgba(6, 182, 212, 0.1);
  color: var(--color-category-weather);
  border-color: rgba(6, 182, 212, 0.3);
}

.category-badge.category--geopolitical {
  background: rgba(249, 115, 22, 0.1);
  color: var(--color-category-geopolitical);
  border-color: rgba(249, 115, 22, 0.3);
}

.category-badge.category--cyber {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-category-cyber);
  border-color: rgba(239, 68, 68, 0.3);
}

.category-badge.category--labor {
  background: rgba(234, 179, 8, 0.1);
  color: var(--color-category-labor);
  border-color: rgba(234, 179, 8, 0.3);
}

.category-badge.category--pandemic {
  background: rgba(34, 197, 94, 0.1);
  color: var(--color-category-pandemic);
  border-color: rgba(34, 197, 94, 0.3);
}

.category-badge.category--infrastructure {
  background: rgba(156, 163, 175, 0.1);
  color: var(--color-category-infrastructure);
  border-color: rgba(156, 163, 175, 0.3);
}

.scenario-name {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.3;
}

.date-range {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.date-range svg {
  flex-shrink: 0;
}

.description {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin: 0;
  flex: 1;
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-3);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--color-border);
}

.metric {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.metric-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.metric-value {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text);
}

.text-mono {
  font-family: var(--font-mono);
}

.run-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  background-color: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-top: var(--spacing-2);
}

.run-btn:hover {
  background-color: var(--color-primary-dark);
  transform: scale(1.02);
}

.run-btn:active {
  transform: scale(0.98);
}

/* Severity border accents */
.scenario-card.severity--low {
  border-left: 3px solid var(--color-low);
}

.scenario-card.severity--medium {
  border-left: 3px solid var(--color-medium);
}

.scenario-card.severity--high {
  border-left: 3px solid var(--color-high);
}

.scenario-card.severity--critical {
  border-left: 3px solid var(--color-critical);
}

/* Responsive */
@media (max-width: 640px) {
  .metrics-row {
    grid-template-columns: 1fr;
    gap: var(--spacing-2);
  }

  .scenario-card {
    padding: var(--spacing-3);
  }

  .scenario-name {
    font-size: var(--text-base);
  }
}
</style>