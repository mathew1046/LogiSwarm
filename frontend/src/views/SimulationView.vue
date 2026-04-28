<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'
import { useSimpleAppStore } from '@/stores/simpleApp'

const simpleAppStore = useSimpleAppStore()

const simulation = computed(() => simpleAppStore.simulation)
const canStart = computed(() => simpleAppStore.hasShipment && simpleAppStore.hasRoutePlan && !simpleAppStore.hasActiveSimulation)

let pollHandle = null

async function startSimulation() {
  const result = await simpleAppStore.startSimulation()
  if (result?.status === 'active') {
    startPolling()
  }
}

async function stopSimulation() {
  await simpleAppStore.stopSimulation()
  stopPolling()
}

function startPolling() {
  stopPolling()
  pollHandle = setInterval(() => {
    simpleAppStore.refreshSimulation()
  }, 2000)
}

function stopPolling() {
  if (pollHandle) {
    clearInterval(pollHandle)
    pollHandle = null
  }
}

onMounted(async () => {
  await simpleAppStore.bootstrap()
  if (simpleAppStore.hasActiveSimulation) {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <ProjectLayout>
    <div class="page-stack">
      <div class="page-header">
        <h1>Simulation</h1>
        <p class="muted">A simulation keeps running until you manually stop it.</p>
      </div>

      <div class="card control-card">
        <div>
          <div class="card-label">Status</div>
          <h2>{{ simulation.status || 'idle' }}</h2>
          <p class="muted">Phase: {{ simulation.phase || 'idle' }}</p>
        </div>
        <div class="control-actions">
          <button class="btn btn--primary" :disabled="!canStart || simpleAppStore.loading" @click="startSimulation">Start Simulation</button>
          <button class="btn btn--danger" :disabled="!simpleAppStore.hasActiveSimulation || simpleAppStore.loading" @click="stopSimulation">Stop Simulation</button>
        </div>
      </div>

      <div class="metrics-grid">
        <div class="metric-card card">
          <div class="card-label">Progress</div>
          <strong>{{ simulation.metrics?.progress_percent ?? 0 }}%</strong>
        </div>
        <div class="metric-card card">
          <div class="card-label">Active Agents</div>
          <strong>{{ simulation.metrics?.active_agents ?? 0 }}</strong>
        </div>
        <div class="metric-card card">
          <div class="card-label">Impacted Places</div>
          <strong>{{ simulation.metrics?.impacted_places ?? 0 }}</strong>
        </div>
        <div class="metric-card card">
          <div class="card-label">Route Risk Score</div>
          <strong>{{ simulation.metrics?.route_risk_score ?? '—' }}</strong>
        </div>
      </div>

      <div class="card">
        <div class="card-label">Live Changes</div>
        <div v-if="!simulation.changes?.length" class="muted">No changes yet.</div>
        <div v-else class="change-list">
          <div v-for="change in simulation.changes" :key="`${change.step}-${change.place_id}`" class="change-item">
            <div class="item-top">
              <strong>Step {{ change.step }} · {{ change.place_name }}</strong>
              <span class="badge" :class="`badge--${change.severity.toLowerCase()}`">{{ change.severity }}</span>
            </div>
            <p class="muted">{{ change.change }}</p>
          </div>
        </div>
      </div>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.page-stack { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; flex-direction: column; gap: 0.35rem; }
.muted { color: var(--color-text-secondary); }
.control-card, .item-top { display: flex; justify-content: space-between; gap: 1rem; }
.control-actions, .metrics-grid { display: grid; gap: 1rem; }
.control-actions { display: flex; flex-wrap: wrap; align-items: center; }
.metrics-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.change-list { display: flex; flex-direction: column; gap: 0.75rem; }
.change-item { border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 0.9rem; background: rgba(15, 23, 42, 0.45); }
@media (max-width: 900px) {
  .metrics-grid { grid-template-columns: 1fr; }
  .control-card { flex-direction: column; }
}
</style>
