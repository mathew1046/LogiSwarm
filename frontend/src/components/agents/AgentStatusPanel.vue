<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAgentStore } from '@/stores/agent'

const props = defineProps({
  compact: {
    type: Boolean,
    default: false
  }
})

const agentStore = useAgentStore()
const expandedAgent = ref(null)
const pulseAgents = ref(new Set())

const agents = computed(() => agentStore.agents)
const loading = computed(() => agentStore.loading)

function getSeverityClass(severity) {
  const s = (severity || 'low').toLowerCase()
  return `severity--${s}`
}

function getSeverityColor(severity) {
  const colors = {
    low: '#22c55e',
    medium: '#f59e0b',
    high: '#f97316',
    critical: '#ef4444'
  }
  return colors[(severity || 'low').toLowerCase()] || colors.low
}

function formatTime(dateStr) {
  if (!dateStr) return 'Never'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return date.toLocaleDateString()
}

function toggleExpand(agentId) {
  expandedAgent.value = expandedAgent.value === agentId ? null : agentId
}

function getConfidencePercent(confidence) {
  return ((confidence || 0) * 100).toFixed(1)
}

watch(() => agentStore.agents, (newAgents, oldAgents) => {
  if (!oldAgents || oldAgents.length === 0) return
  
  newAgents.forEach((newAgent, index) => {
    const oldAgent = oldAgents[index]
    if (oldAgent && newAgent.last_cycle_at !== oldAgent.last_cycle_at) {
      pulseAgents.value.add(newAgent.region_id)
      setTimeout(() => {
        pulseAgents.value.delete(newAgent.region_id)
      }, 2000)
    }
  })
}, { deep: true })

onMounted(async () => {
  await agentStore.fetchAgents()
})

function isPulsing(regionId) {
  return pulseAgents.value.has(regionId)
}
</script>

<template>
  <div class="agent-status-panel">
    <div class="panel-header">
      <h2>Agent Status</h2>
      <div class="panel-stats">
        <span class="stat">
          <span class="stat__value">{{ agents.length }}</span>
          <span class="stat__label">Active</span>
        </span>
        <span class="stat">
          <span class="stat__value severity--critical">{{ agentStore.highRiskAgents.length }}</span>
          <span class="stat__label">High Risk</span>
        </span>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="loading__spinner"></div>
    </div>

    <div v-else class="agents-grid" :class="{ 'agents-grid--compact': compact }">
      <div 
        v-for="agent in agents" 
        :key="agent.region_id"
        :class="['agent-card', { 
          'agent-card--expanded': expandedAgent === agent.region_id,
          'agent-card--pulse': isPulsing(agent.region_id)
        }]"
        @click="toggleExpand(agent.region_id)"
      >
        <div class="agent-card__header">
          <div class="agent-card__title">
            <h3>{{ agent.region_name }}</h3>
            <span 
              :class="['status-badge', getSeverityClass(agent.last_assessment?.severity)]"
              :style="{ backgroundColor: getSeverityColor(agent.last_assessment?.severity) }"
            >
              {{ agent.last_assessment?.severity || 'LOW' }}
            </span>
          </div>
          <div class="agent-card__status">
            <span :class="['status-dot', { 'status-dot--active': agent.running }]"></span>
            {{ agent.running ? 'Running' : 'Stopped' }}
          </div>
        </div>

        <div class="agent-card__metrics">
          <div class="metric">
            <div class="metric__label">Confidence</div>
            <div class="metric__value">
              {{ getConfidencePercent(agent.last_assessment?.confidence) }}%
            </div>
            <div class="metric__bar">
              <div 
                class="metric__fill" 
                :style="{ 
                  width: getConfidencePercent(agent.last_assessment?.confidence) + '%',
                  backgroundColor: getSeverityColor(agent.last_assessment?.severity)
                }"
              ></div>
            </div>
          </div>
          <div class="metric">
            <div class="metric__label">Last Cycle</div>
            <div class="metric__value metric__value--small">
              {{ formatTime(agent.last_cycle_at) }}
            </div>
          </div>
        </div>

        <div v-if="expandedAgent === agent.region_id" class="agent-card__details">
          <h4>Reasoning</h4>
          <p v-if="agent.last_assessment?.reasoning" class="reasoning-text">
            {{ agent.last_assessment.reasoning }}
          </p>
          <p v-else class="reasoning-text reasoning-text--empty">
            No reasoning available yet.
          </p>

          <h4 v-if="agent.last_assessment?.recommended_actions?.length">Recommended Actions</h4>
          <ul v-if="agent.last_assessment?.recommended_actions?.length" class="actions-list">
            <li v-for="(action, index) in agent.last_assessment.recommended_actions" :key="index">
              {{ action }}
            </li>
          </ul>

          <h4>Signal Sources</h4>
          <div class="signal-sources">
            <span v-for="signal in (agent.last_assessment?.signals || [])" :key="signal" class="signal-tag">
              {{ signal }}
            </span>
            <span v-if="!agent.last_assessment?.signals?.length" class="signal-tag signal-tag--empty">
              No active signals
            </span>
          </div>
        </div>

        <div class="agent-card__expand-hint">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 9l-7 7-7-7" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-status-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-4);
}

.panel-header h2 {
  margin: 0;
}

.panel-stats {
  display: flex;
  gap: var(--spacing-4);
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat__value {
  font-size: var(--text-xl);
  font-weight: 700;
}

.stat__label {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-4);
  overflow-y: auto;
}

.agents-grid--compact {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}

.agent-card {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.agent-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}

.agent-card--pulse {
  animation: pulse-border 2s ease-out;
}

@keyframes pulse-border {
  0% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.5);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
  }
}

.agent-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-3);
}

.agent-card__title {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.agent-card__title h3 {
  margin: 0;
  font-size: var(--text-base);
}

.status-badge {
  display: inline-flex;
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  color: white;
}

.agent-card__status {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background-color: var(--color-text-tertiary);
}

.status-dot--active {
  background-color: var(--color-success);
  animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.agent-card__metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-3);
}

.metric__label {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
}

.metric__value {
  font-size: var(--text-lg);
  font-weight: 600;
}

.metric__value--small {
  font-size: var(--text-sm);
  font-weight: 400;
}

.metric__bar {
  height: 4px;
  background-color: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-top: var(--spacing-1);
}

.metric__fill {
  height: 100%;
  transition: width var(--transition-normal);
}

.agent-card__details {
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border);
}

.agent-card__details h4 {
  margin: 0 0 var(--spacing-2);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.reasoning-text {
  font-size: var(--text-sm);
  color: var(--color-text);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--spacing-4);
}

.reasoning-text--empty {
  font-style: italic;
  color: var(--color-text-tertiary);
}

.actions-list {
  list-style: disc;
  padding-left: var(--spacing-4);
  margin-bottom: var(--spacing-4);
}

.actions-list li {
  font-size: var(--text-sm);
  margin-bottom: var(--spacing-1);
}

.signal-sources {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-1);
}

.signal-tag {
  padding: var(--spacing-1) var(--spacing-2);
  background-color: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
}

.signal-tag--empty {
  color: var(--color-text-tertiary);
}

.agent-card__expand-hint {
  position: absolute;
  bottom: var(--spacing-2);
  right: var(--spacing-2);
  color: var(--color-text-tertiary);
  transition: transform var(--transition-fast);
}

.agent-card:hover .agent-card__expand-hint {
  transform: translateY(2px);
}

.severity--low { color: var(--color-low); }
.severity--medium { color: var(--color-medium); }
.severity--high { color: var(--color-high); }
.severity--critical { color: var(--color-critical); }
</style>