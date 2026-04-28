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
const searchQuery = ref('')
const activeTiers = ref([1, 2, 3])
const collapsedTiers = ref(new Set())

const agents = computed(() => agentStore.agents)
const loading = computed(() => agentStore.loading)

const tier1Agents = computed(() => agents.value.filter(a => (a.tier || 1) === 1))
const tier2Agents = computed(() => agents.value.filter(a => a.tier === 2))
const tier3Agents = computed(() => agents.value.filter(a => a.tier === 3))

const filteredAgents = computed(() => {
  let result = agents.value
  if (activeTiers.value.length > 0 && activeTiers.value.length < 3) {
    result = result.filter(a => activeTiers.value.includes(a.tier || 1))
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(a =>
      a.region_id?.toLowerCase().includes(q) ||
      a.region_name?.toLowerCase().includes(q)
    )
  }
  return result
})

const tier1Filtered = computed(() => filteredAgents.value.filter(a => (a.tier || 1) === 1))
const tier2Filtered = computed(() => filteredAgents.value.filter(a => a.tier === 2))
const tier3Filtered = computed(() => filteredAgents.value.filter(a => a.tier === 3))

const stats = computed(() => ({
  total: agents.value.length,
  running: agents.value.filter(a => a.running).length,
  highRisk: agentStore.highRiskAgents?.length || 0,
  degraded: agentStore.degradedAgents?.length || 0,
  tier1: tier1Agents.value.length,
  tier2: tier2Agents.value.length,
  tier3: tier3Agents.value.length,
}))

function getSeverityClass(severity) {
  const s = (severity || 'low').toLowerCase()
  return `badge--${s}`
}

function getSeverityColor(severity) {
  const colors = {
    low: 'var(--color-low)',
    medium: 'var(--color-medium)',
    high: 'var(--color-high)',
    critical: 'var(--color-critical)'
  }
  return colors[(severity || 'low').toLowerCase()] || colors.low
}

function getRiskCardClass(severity) {
  return `risk-${(severity || 'low').toLowerCase()}`
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

function isPulsing(regionId) {
  return pulseAgents.value.has(regionId)
}

function toggleTier(tier) {
  const idx = activeTiers.value.indexOf(tier)
  if (idx > -1) {
    activeTiers.value.splice(idx, 1)
  } else {
    activeTiers.value.push(tier)
  }
}

function toggleCollapse(tier) {
  if (collapsedTiers.value.has(tier)) {
    collapsedTiers.value.delete(tier)
  } else {
    collapsedTiers.value.add(tier)
  }
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
</script>

<template>
  <div class="agent-status-panel">
    <div class="panel-header">
      <h2>Agent Status</h2>
      <div class="panel-stats">
        <span class="stat">
          <span class="stat__value text-mono">{{ stats.total }}</span>
          <span class="stat__label">Total</span>
        </span>
        <span class="stat">
          <span class="stat__value text-success text-mono">{{ stats.running }}</span>
          <span class="stat__label">Running</span>
        </span>
        <span class="stat">
          <span class="stat__value text-critical text-mono">{{ stats.highRisk }}</span>
          <span class="stat__label">High Risk</span>
        </span>
        <span v-if="stats.degraded > 0" class="stat">
          <span class="stat__value text-warning text-mono">{{ stats.degraded }}</span>
          <span class="stat__label">Degraded</span>
        </span>
      </div>
    </div>

    <div class="panel-controls">
      <input
        v-model="searchQuery"
        type="text"
        class="search-input input"
        placeholder="Search agents..."
      />
      <div class="tier-filters">
        <button
          :class="['tier-btn', { 'tier-btn--active': activeTiers.includes(1) }]"
          @click="toggleTier(1)"
        >
          T1 <span class="tier-count">{{ stats.tier1 }}</span>
        </button>
        <button
          :class="['tier-btn', { 'tier-btn--active': activeTiers.includes(2) }]"
          @click="toggleTier(2)"
        >
          T2 <span class="tier-count">{{ stats.tier2 }}</span>
        </button>
        <button
          :class="['tier-btn', { 'tier-btn--active': activeTiers.includes(3) }]"
          @click="toggleTier(3)"
        >
          T3 <span class="tier-count">{{ stats.tier3 }}</span>
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="loading__spinner"></div>
    </div>

    <div v-else class="agents-scroll">
      <template v-if="tier1Filtered.length > 0">
        <div class="tier-section">
          <button class="tier-header" @click="toggleCollapse(1)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: collapsedTiers.has(1) ? 'rotate(-90deg)' : 'rotate(0)' }"><path d="M6 9l6 6 6-6"/></svg>
            <span class="tier-header__label">Regional Agents</span>
            <span class="tier-header__badge tier-badge--1">{{ tier1Filtered.length }}</span>
          </button>
          <div v-show="!collapsedTiers.has(1)" class="agents-grid" :class="{ 'agents-grid--compact': compact }">
            <div
              v-for="agent in tier1Filtered"
              :key="agent.region_id"
              :class="['agent-card', 'card', 'card--glass', getRiskCardClass(agent.last_assessment?.severity), 'risk-border', {
                'agent-card--expanded': expandedAgent === agent.region_id,
                'agent-card--pulse': isPulsing(agent.region_id)
              }]"
              @click="toggleExpand(agent.region_id)"
            >
              <div class="agent-card__tier-badge tier-badge--1">T1</div>
              <div class="agent-card__header">
                <div class="agent-card__title">
                  <h3>{{ agent.region_name }}</h3>
                  <span :class="['badge', getSeverityClass(agent.last_assessment?.severity)]">
                    {{ agent.last_assessment?.severity || 'LOW' }}
                  </span>
                </div>
                <div class="agent-card__status">
                  <span :class="['status-dot', { 'status-dot--active': agent.running }]"></span>
                  <span class="status-text">{{ agent.running ? 'Running' : 'Stopped' }}</span>
                </div>
              </div>
              <div class="agent-card__metrics">
                <div class="metric">
                  <div class="metric__label">Confidence</div>
                  <div class="metric__value text-mono">{{ getConfidencePercent(agent.last_assessment?.confidence) }}%</div>
                  <div class="metric__bar"><div class="metric__fill" :style="{ width: getConfidencePercent(agent.last_assessment?.confidence) + '%', backgroundColor: getSeverityColor(agent.last_assessment?.severity) }"></div></div>
                </div>
                <div class="metric">
                  <div class="metric__label">Last Cycle</div>
                  <div class="metric__value metric__value--small text-mono">{{ formatTime(agent.last_cycle_at) }}</div>
                </div>
              </div>
              <div v-if="expandedAgent === agent.region_id" class="agent-card__details fade-in">
                <h4>Reasoning</h4>
                <p v-if="agent.last_assessment?.reasoning" class="reasoning-text">{{ agent.last_assessment.reasoning }}</p>
                <p v-else class="reasoning-text reasoning-text--empty">No reasoning available yet.</p>
                <h4 v-if="agent.last_assessment?.recommended_actions?.length">Recommended Actions</h4>
                <ul v-if="agent.last_assessment?.recommended_actions?.length" class="actions-list">
                  <li v-for="(action, index) in agent.last_assessment.recommended_actions" :key="index">{{ action }}</li>
                </ul>
              </div>
              <div class="agent-card__expand-hint">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: expandedAgent === agent.region_id ? 'rotate(180deg)' : 'rotate(0)' }"><path d="M19 9l-7 7-7-7" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-if="tier2Filtered.length > 0">
        <div class="tier-section">
          <button class="tier-header" @click="toggleCollapse(2)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: collapsedTiers.has(2) ? 'rotate(-90deg)' : 'rotate(0)' }"><path d="M6 9l6 6 6-6"/></svg>
            <span class="tier-header__label">Port Clusters &amp; Chokepoints</span>
            <span class="tier-header__badge tier-badge--2">{{ tier2Filtered.length }}</span>
          </button>
          <div v-show="!collapsedTiers.has(2)" class="agents-grid" :class="{ 'agents-grid--compact': compact }">
            <div v-for="agent in tier2Filtered" :key="agent.region_id"
              :class="['agent-card', 'card', 'card--glass', getRiskCardClass(agent.last_assessment?.severity), { 'agent-card--expanded': expandedAgent === agent.region_id, 'agent-card--pulse': isPulsing(agent.region_id) }]"
              @click="toggleExpand(agent.region_id)">
              <div class="agent-card__tier-badge tier-badge--2">T2</div>
              <div class="agent-card__header">
                <div class="agent-card__title"><h3>{{ agent.region_name }}</h3><span :class="['badge', getSeverityClass(agent.last_assessment?.severity)]">{{ agent.last_assessment?.severity || 'LOW' }}</span></div>
                <div class="agent-card__status"><span :class="['status-dot', { 'status-dot--active': agent.running }]"></span></div>
              </div>
              <div class="agent-card__metrics">
                <div class="metric"><div class="metric__label">Confidence</div><div class="metric__value text-mono">{{ getConfidencePercent(agent.last_assessment?.confidence) }}%</div><div class="metric__bar"><div class="metric__fill" :style="{ width: getConfidencePercent(agent.last_assessment?.confidence) + '%', backgroundColor: getSeverityColor(agent.last_assessment?.severity) }"></div></div></div>
                <div class="metric"><div class="metric__label">Last Cycle</div><div class="metric__value metric__value--small text-mono">{{ formatTime(agent.last_cycle_at) }}</div></div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-if="tier3Filtered.length > 0">
        <div class="tier-section">
          <button class="tier-header" @click="toggleCollapse(3)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: collapsedTiers.has(3) ? 'rotate(-90deg)' : 'rotate(0)' }"><path d="M6 9l6 6 6-6"/></svg>
            <span class="tier-header__label">Individual Ports &amp; Hubs</span>
            <span class="tier-header__badge tier-badge--3">{{ tier3Filtered.length }}</span>
          </button>
          <div v-show="!collapsedTiers.has(3)" class="agents-grid agents-grid--compact" :class="{ 'agents-grid--mini': !compact }">
            <div v-for="agent in tier3Filtered" :key="agent.region_id"
              :class="['agent-card', 'card', 'card--glass', 'agent-card--small', getRiskCardClass(agent.last_assessment?.severity), { 'agent-card--pulse': isPulsing(agent.region_id) }]"
              @click="toggleExpand(agent.region_id)">
              <div class="agent-card__tier-badge tier-badge--3">T3</div>
              <span class="agent-card__minititle">{{ agent.region_name }}</span>
              <span :class="['badge', 'badge--sm', getSeverityClass(agent.last_assessment?.severity)]">{{ agent.last_assessment?.severity || 'LOW' }}</span>
              <span class="agent-card__conf text-mono">{{ getConfidencePercent(agent.last_assessment?.confidence) }}%</span>
            </div>
          </div>
        </div>
      </template>

      <div v-if="filteredAgents.length === 0 && !loading" class="empty-state">
        <p class="empty-state__title">No agents found</p>
        <p class="empty-state__text">Adjust your search or tier filters.</p>
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
  font-size: var(--text-xl);
  font-weight: 600;
}

.panel-stats {
  display: flex;
  gap: var(--spacing-6);
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat__value {
  font-size: var(--text-2xl);
  font-weight: 700;
  font-family: var(--font-mono);
}

.text-critical { color: var(--color-critical); }
.text-success { color: var(--color-success); }
.text-warning { color: var(--color-warning); }
.text-mono { font-family: var(--font-mono); }

.stat__label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.panel-controls {
  display: flex;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
  align-items: center;
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.tier-filters {
  display: flex;
  gap: var(--spacing-2);
}

.tier-btn {
  padding: var(--spacing-1) var(--spacing-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.tier-btn--active {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-color: var(--color-primary);
}

.tier-btn:hover:not(.tier-btn--active) {
  background: var(--color-bg-tertiary);
  border-color: var(--color-primary-light);
}

.tier-count {
  font-size: var(--text-xs);
  opacity: 0.7;
  font-family: var(--font-mono);
}

.agents-scroll {
  overflow-y: auto;
  flex: 1;
}

.tier-section {
  margin-bottom: var(--spacing-4);
}

.tier-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  width: 100%;
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  cursor: pointer;
  margin-bottom: var(--spacing-3);
  transition: all var(--transition-fast);
}

.tier-header:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-primary-light);
}

.tier-header svg {
  transition: transform var(--transition-fast);
  flex-shrink: 0;
}

.tier-header__label {
  font-size: var(--text-sm);
  font-weight: 600;
  flex: 1;
  text-align: left;
}

.tier-header__badge {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.tier-badge--1 {
  background: rgba(59, 130, 246, 0.15);
  color: var(--color-primary-light);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.tier-badge--2 {
  background: rgba(99, 102, 241, 0.15);
  color: var(--color-secondary);
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.tier-badge--3 {
  background: rgba(6, 182, 212, 0.15);
  color: var(--color-info);
  border: 1px solid rgba(6, 182, 212, 0.3);
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-3);
}

.agents-grid--compact {
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}

.agents-grid--mini {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}

.agent-card {
  padding: var(--spacing-4);
  cursor: pointer;
  position: relative;
  transition: all var(--transition-fast);
}

.agent-card--small {
  padding: var(--spacing-3);
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.agent-card__tier-badge {
  position: absolute;
  top: var(--spacing-1);
  right: var(--spacing-2);
  font-size: 10px;
  font-weight: 600;
  font-family: var(--font-mono);
  padding: 1px 4px;
  border-radius: var(--radius-sm);
  line-height: 1.2;
}

.agent-card--small .agent-card__tier-badge {
  position: static;
  font-size: 9px;
}

.agent-card__minititle {
  font-size: var(--text-sm);
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-card__conf {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.agent-card--pulse {
  animation: cardPulse 2s ease-out;
}

@keyframes cardPulse {
  0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
  100% { box-shadow: 0 0 0 0 transparent; }
}

.agent-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-3);
  padding-right: var(--spacing-6);
}

.agent-card__title {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.agent-card__title h3 {
  margin: 0;
  font-size: var(--text-base);
  font-weight: 600;
}

.agent-card__status {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--text-xs);
}

.status-text {
  color: var(--color-text-tertiary);
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
  height: 3px;
  background-color: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-top: var(--spacing-1);
}

.metric__fill {
  height: 100%;
  transition: width var(--transition-normal);
  border-radius: var(--radius-full);
}

.agent-card__details {
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border);
}

.agent-card__details h4 {
  margin: 0 0 var(--spacing-2);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
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

.risk-border {
  border-left: 3px solid var(--color-border);
}
.risk-low { border-left-color: var(--color-low); }
.risk-medium { border-left-color: var(--color-medium); }
.risk-high { border-left-color: var(--color-high); }
.risk-critical { border-left-color: var(--color-critical); }

.badge--sm {
  font-size: 10px;
  padding: 1px 6px;
}

@media (max-width: 768px) {
  .panel-stats {
    gap: var(--spacing-3);
  }
  .panel-controls {
    flex-direction: column;
  }
  .search-input {
    min-width: unset;
    width: 100%;
  }
  .agents-grid, .agents-grid--compact, .agents-grid--mini {
    grid-template-columns: 1fr;
  }
}
</style>
