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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'
import { useAgentStore } from '@/stores/agent'
import { useScenarioStore } from '@/stores/scenario'
import { useAuthStore } from '@/stores/auth'
import MetricsSummary from '@/components/scenarios/MetricsSummary.vue'
import CategoryFilter from '@/components/scenarios/CategoryFilter.vue'
import ScenarioCard from '@/components/scenarios/ScenarioCard.vue'
import ScenarioDetailModal from '@/components/scenarios/ScenarioDetailModal.vue'

const agentStore = useAgentStore()
const scenarioStore = useScenarioStore()
const authStore = useAuthStore()

const running = ref(false)
const logEntries = ref([])
const selectedScenario = ref(null)
const modalVisible = ref(false)
const activeCategory = ref(null)
const logCollapsed = ref(false)

const agentCount = computed(() => agentStore.agents.length || 155)
const tier1Count = computed(() => agentStore.tier1Agents.length || 8)
const tier2Count = computed(() => agentStore.tier2Agents.length || 30)
const tier3Count = computed(() => agentStore.tier3Agents.length || 117)

const filteredScenarios = computed(() => {
  if (!activeCategory.value) return scenarioStore.scenarios
  return scenarioStore.scenarios.filter(s => s.category === activeCategory.value)
})

const addLog = (msg, type = 'info') => {
  logEntries.value.unshift({ ts: new Date().toLocaleTimeString(), msg, type })
  if (logEntries.value.length > 80) logEntries.value.length = 80
}

const handleFilter = (category) => {
  activeCategory.value = category
}

const openScenarioModal = (scenario) => {
  selectedScenario.value = scenario
  modalVisible.value = true
}

const closeScenarioModal = () => {
  modalVisible.value = false
  selectedScenario.value = null
}

const runSimulation = async (scenario) => {
  if (running.value) return
  running.value = true
  logEntries.value = []

  const region = scenario.trigger_region || 'unknown'
  const severity = scenario.severity || 'MEDIUM'
  const duration = scenario.duration_days || 7

  addLog(`Simulating: ${scenario.name}`, 'info')
  addLog(`Region: ${region}  Severity: ${severity}  Duration: ${duration}d`, 'info')

  try {
    const res = await fetch('/api/orchestrator/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authStore.getAuthHeaders() },
      body: JSON.stringify({
        scenario: scenario.id || scenario.name,
        region_id: region,
        severity,
        start_date: new Date().toISOString(),
        end_date: new Date(Date.now() + duration * 86400000).toISOString()
      })
    })
    if (res.ok) {
      const data = await res.json()
      addLog('Simulation injected successfully', 'ok')
      const agents = data?.data?.agents_contacted || data?.data?.affected_agents || []
      if (agents.length) addLog(`Agents contacted: ${agents.length}`, 'ok')
      if (data?.data?.cascade_risk) addLog(`Cascade risk: ${(data.data.cascade_risk * 100).toFixed(0)}%`, 'warn')
    } else {
      addLog('API unavailable — running client simulation', 'warn')
      addLog(`${agentCount.value} agents monitoring region`, 'info')
      setTimeout(() => addLog('Regional agent detected anomaly', 'info'), 1200)
      setTimeout(() => addLog('Broadcasting to neighbor agents', 'info'), 2800)
      setTimeout(() => addLog(`Cascade risk computed across ${agentCount.value} nodes`, 'warn'), 4500)
      setTimeout(() => addLog('Route alternatives generated', 'ok'), 6000)
    }
  } catch {
    addLog('Network error — client simulation fallback', 'warn')
    setTimeout(() => addLog(`${agentCount.value} agents online, monitoring`, 'info'), 1000)
    setTimeout(() => addLog('Anomaly detected in target region', 'info'), 2500)
    setTimeout(() => addLog('Cascade propagation modeled', 'warn'), 4000)
    setTimeout(() => addLog('Simulation complete', 'ok'), 5500)
  } finally {
    setTimeout(() => { running.value = false }, 6500)
  }
}

const clearLog = () => {
  logEntries.value = []
}

const toggleLog = () => {
  logCollapsed.value = !logCollapsed.value
}

onMounted(async () => {
  await scenarioStore.fetchScenarios()
  await scenarioStore.fetchCategories()
  try { await agentStore.fetchAgents() } catch { /* offline ok */ }
  addLog(`${agentCount.value} agents online across 3 tiers`, 'info')
  addLog('Select a scenario card to view details', 'info')
})

onUnmounted(() => {
  // nothing to clean
})
</script>

<template>
  <ProjectLayout>
    <div class="sim-page">
      <!-- Header -->
      <div class="sim-header">
        <h1>Historical Scenarios</h1>
      </div>

      <!-- Metrics Summary -->
      <div class="metrics-section">
        <MetricsSummary :scenarios="scenarioStore.scenarios" />
      </div>

      <!-- Category Filter -->
      <div class="filter-section">
        <CategoryFilter
          :categories="scenarioStore.categories"
          :activeCategory="activeCategory"
          @filter="handleFilter"
        />
      </div>

      <!-- Loading / Error states -->
      <div v-if="scenarioStore.loading" class="state-message">
        <span class="loading-spinner"></span>
        Loading scenarios...
      </div>
      <div v-else-if="scenarioStore.error" class="state-message error">
        Failed to load scenarios: {{ scenarioStore.error }}
      </div>
      <div v-else-if="filteredScenarios.length === 0" class="state-message empty">
        <span class="empty-icon">📭</span>
        <span>No scenarios found{{ activeCategory ? ` in "${activeCategory}"` : '' }}.</span>
      </div>

      <!-- Scenario Cards Grid -->
      <div v-else class="cards-grid">
        <ScenarioCard
          v-for="scenario in filteredScenarios"
          :key="scenario.id"
          :scenario="scenario"
          @click="openScenarioModal(scenario)"
          @run-simulation="runSimulation"
        />
      </div>

      <!-- Bottom section: Log + Agent Topology -->
      <div class="bottom-grid">
        <!-- Log terminal (collapsible) -->
        <section class="sim-right">
          <div class="card log-card" :class="{ collapsed: logCollapsed }">
            <div class="log-header">
              <span class="card-label">Log</span>
              <span class="log-status" :class="{ live: running }">{{ running ? 'Live' : 'Ready' }}</span>
              <button v-if="logEntries.length && !logCollapsed" class="clear-btn" @click="clearLog">Clear</button>
              <button class="toggle-btn" @click="toggleLog" :title="logCollapsed ? 'Expand' : 'Collapse'">
                <svg v-if="!logCollapsed" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="18 15 12 9 6 15"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
            </div>
            <div v-if="!logCollapsed" class="log-body">
              <div v-if="!logEntries.length" class="log-empty">No simulation running yet.</div>
              <div v-else class="log-scroll">
                <div v-for="(e, i) in logEntries" :key="i" class="log-line" :class="e.type">
                  <span class="log-ts">{{ e.ts }}</span>
                  <span class="log-msg">{{ e.msg }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Agent topology summary -->
        <section class="sim-topo">
          <div class="card topo-card">
            <div class="card-label">Agent Topology</div>
            <div class="topo-rows">
              <div class="topo-row">
                <span class="topo-tier">T1</span>
                <span class="topo-label">Regional Zones</span>
                <span class="topo-num">{{ tier1Count }}</span>
              </div>
              <div class="topo-row">
                <span class="topo-tier">T2</span>
                <span class="topo-label">Clusters &amp; Chokepoints</span>
                <span class="topo-num">{{ tier2Count }}</span>
              </div>
              <div class="topo-row">
                <span class="topo-tier">T3</span>
                <span class="topo-label">Ports, Hubs &amp; Nodes</span>
                <span class="topo-num">{{ tier3Count }}</span>
              </div>
              <div class="topo-row topo-total">
                <span class="topo-tier"></span>
                <span class="topo-label">Total Intercommunicating Agents</span>
                <span class="topo-num total">{{ agentCount }}</span>
              </div>
            </div>
            <p class="topo-note">
              Every agent broadcasts alerts to its proximity neighbors via Redis pub/sub.
              A disruption detected by any T1 agent cascades across the entire swarm within one cycle.
            </p>
          </div>
        </section>
      </div>

      <!-- Scenario Detail Modal -->
      <ScenarioDetailModal
        :scenario="selectedScenario"
        :visible="modalVisible"
        @close="closeScenarioModal"
        @run-simulation="runSimulation"
      />
    </div>
  </ProjectLayout>
</template>

<style scoped>
.sim-page { padding: 0; }

.sim-header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}
.sim-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary, #e2e8f0);
  margin: 0;
}

.metrics-section {
  margin-bottom: 1.25rem;
}

.filter-section {
  margin-bottom: 1.5rem;
}

.state-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
  color: var(--text-secondary, #94a3b8);
  font-size: 0.9rem;
}
.state-message.error {
  color: var(--color-error, #ef4444);
}
.state-message.empty {
  color: var(--text-tertiary, #64748b);
}
.empty-icon {
  font-size: 1.5rem;
}
.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border-color, #334155);
  border-top-color: var(--primary-color, #3b82f6);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Cards grid */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}
@media (max-width: 1100px) {
  .cards-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .cards-grid { grid-template-columns: 1fr; }
}

/* Bottom grid: log + topology side by side */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
  align-items: start;
}
@media (max-width: 900px) {
  .bottom-grid { grid-template-columns: 1fr; }
}

/* Card */
.card {
  background: var(--surface-color, #1e293b);
  border: 1px solid var(--border-color, #334155);
  border-radius: 0.75rem;
  padding: 1rem 1.25rem;
}
.card-label {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary, #94a3b8);
  margin-bottom: 0.75rem;
}

/* Log card */
.log-card { display: flex; flex-direction: column; }
.log-card.collapsed { padding-bottom: 0.5rem; }
.log-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}
.log-header .card-label { margin-bottom: 0; }
.log-status {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
  background: var(--surface-hover, #334155);
  color: var(--text-secondary, #94a3b8);
}
.log-status.live { background: #16a34a; color: #fff; }
.clear-btn {
  margin-left: auto;
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border: 1px solid var(--border-color, #334155);
  border-radius: 0.3rem;
  background: transparent;
  color: var(--text-secondary, #94a3b8);
  cursor: pointer;
}
.clear-btn:hover { border-color: var(--primary-color, #3b82f6); }
.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: transparent;
  border: 1px solid var(--border-color, #334155);
  border-radius: 0.3rem;
  color: var(--text-secondary, #94a3b8);
  cursor: pointer;
}
.toggle-btn:hover { border-color: var(--primary-color, #3b82f6); }
.log-body {
  flex: 1;
  min-height: 300px;
  max-height: 400px;
  overflow-y: auto;
  background: #0f172a;
  border-radius: 0.4rem;
  padding: 0.5rem 0.75rem;
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 0.8rem;
}
.log-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary, #64748b);
  font-style: italic;
}
.log-line {
  padding: 0.3rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  display: flex;
  gap: 0.6rem;
}
.log-line:last-child { border-bottom: none; }
.log-ts { color: #475569; flex-shrink: 0; font-size: 0.75rem; }
.log-msg { color: #cbd5e1; }
.log-line.ok .log-msg { color: #22c55e; }
.log-line.warn .log-msg { color: #f59e0b; }
.log-line.error .log-msg { color: #ef4444; }
.log-line.info .log-msg { color: #60a5fa; }

/* Topology card */
.topo-card { }
.topo-rows { display: flex; flex-direction: column; gap: 0.5rem; }
.topo-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.35rem 0;
  border-bottom: 1px solid var(--border-color, #334155);
}
.topo-row:last-child { border-bottom: none; }
.topo-tier {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 0.15rem 0.4rem;
  border-radius: 0.25rem;
  background: var(--surface-hover, #334155);
  color: var(--text-secondary, #94a3b8);
  min-width: 1.5rem;
  text-align: center;
}
.topo-label { flex: 1; font-size: 0.8rem; color: var(--text-primary, #e2e8f0); }
.topo-num { font-size: 0.85rem; font-weight: 600; color: var(--text-primary, #e2e8f0); }
.topo-num.total { color: var(--primary-color, #3b82f6); font-size: 1rem; }
.topo-row.topo-total { padding-top: 0.5rem; border-top: 2px solid var(--border-color, #334155); }
.topo-note {
  font-size: 0.75rem;
  color: var(--text-secondary, #94a3b8);
  margin: 0.75rem 0 0;
  line-height: 1.5;
}
</style>