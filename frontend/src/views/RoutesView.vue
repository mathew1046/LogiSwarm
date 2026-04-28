<script setup>
import { computed, onMounted } from 'vue'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'
import { useSimpleAppStore } from '@/stores/simpleApp'

const simpleAppStore = useSimpleAppStore()
const routePlan = computed(() => simpleAppStore.routePlan)
const recommendedRoute = computed(() => simpleAppStore.recommendedRoute)

onMounted(async () => {
  await simpleAppStore.bootstrap()
})
</script>

<template>
  <ProjectLayout>
    <div class="page-stack">
      <div class="page-header">
        <h1>Routes</h1>
        <p class="muted">Rebuilt from scratch: 10 agents exchange mocked weather/news signals and reason over route options.</p>
      </div>

      <div v-if="!routePlan" class="card muted">
        No route plan yet. Configure a shipment in Dashboard first.
      </div>

      <template v-else>
        <div class="card">
          <div class="card-label">Recommended Route</div>
          <h2>{{ recommendedRoute.name }}</h2>
          <p class="muted">{{ routePlan.summary }}</p>
          <div class="stats-grid">
            <div class="stat-card">
              <span class="card-label">Waypoints</span>
              <strong>{{ recommendedRoute.waypoints.join(' → ') }}</strong>
            </div>
            <div class="stat-card">
              <span class="card-label">Risk Score</span>
              <strong>{{ recommendedRoute.risk_score }}</strong>
            </div>
            <div class="stat-card">
              <span class="card-label">Est. Hours</span>
              <strong>{{ recommendedRoute.estimated_hours }}</strong>
            </div>
            <div class="stat-card">
              <span class="card-label">Cost Index</span>
              <strong>{{ recommendedRoute.estimated_cost_index }}</strong>
            </div>
          </div>
        </div>

        <div class="route-grid">
          <div class="card">
            <div class="card-label">Agent Intercommunication</div>
            <div class="list-stack">
              <div v-for="message in recommendedRoute.intercommunication" :key="`${message.from}-${message.to}`" class="list-item">
                <strong>{{ message.from }} → {{ message.to }}</strong>
                <p class="muted">{{ message.message }}</p>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-label">Agent Reasoning</div>
            <div class="list-stack">
              <div v-for="agent in recommendedRoute.agent_reasoning" :key="agent.agent_id" class="list-item">
                <div class="item-top">
                  <strong>{{ agent.place_name }}</strong>
                  <span class="badge" :class="`badge--${agent.severity.toLowerCase()}`">{{ agent.severity }}</span>
                </div>
                <p class="muted">Weather: {{ agent.weather }}</p>
                <p class="muted">News: {{ agent.news }}</p>
                <p>{{ agent.reasoning }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-label">Alternative Routes</div>
          <div class="route-options">
            <div v-for="option in routePlan.alternatives" :key="option.route_id" class="option-card">
              <h3>{{ option.name }}</h3>
              <p class="muted">{{ option.waypoints.join(' → ') }}</p>
              <p>Risk {{ option.risk_score }} · {{ option.estimated_hours }}h · Cost {{ option.estimated_cost_index }}</p>
            </div>
          </div>
        </div>
      </template>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.page-stack { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; flex-direction: column; gap: 0.35rem; }
.muted { color: var(--color-text-secondary); }
.stats-grid, .route-grid, .route-options { display: grid; gap: 1rem; }
.stats-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.route-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.route-options { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.stat-card, .list-item, .option-card { border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 0.9rem; background: rgba(15, 23, 42, 0.45); }
.list-stack { display: flex; flex-direction: column; gap: 0.75rem; }
.item-top { display: flex; justify-content: space-between; gap: 1rem; }
@media (max-width: 1000px) {
  .stats-grid, .route-grid, .route-options { grid-template-columns: 1fr; }
}
</style>
