<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'
import { useSimpleAppStore } from '@/stores/simpleApp'

const router = useRouter()
const simpleAppStore = useSimpleAppStore()

const shipmentLabel = computed(() => {
  if (!simpleAppStore.shipment) return 'No shipment configured'
  return `${simpleAppStore.shipment.origin_name} → ${simpleAppStore.shipment.destination_name}`
})

const summaryCards = computed(() => [
  { label: 'Places', value: simpleAppStore.places.length },
  { label: 'Agents', value: simpleAppStore.agents.length },
  { label: 'Route Options', value: simpleAppStore.routePlan?.alternatives?.length || 0 },
  { label: 'Reports', value: simpleAppStore.reports.length }
])

onMounted(async () => {
  await simpleAppStore.bootstrap()
})
</script>

<template>
  <ProjectLayout>
    <div class="page-stack">
      <section class="hero card">
        <div>
          <div class="eyebrow">Simple Logistics Control</div>
          <h1>10 agents. One shipment. Clear route decisions.</h1>
          <p class="hero-text">
            Configure a shipment, inspect live agent signals, run a persistent simulation,
            and review the recommended route produced by inter-agent reasoning.
          </p>
        </div>
        <div class="hero-actions">
          <button class="btn btn--primary" @click="router.push('/dashboard')">Open Dashboard</button>
          <button class="btn btn--secondary" @click="router.push('/routes')">Open Routes</button>
        </div>
      </section>

      <section class="summary-grid">
        <div v-for="card in summaryCards" :key="card.label" class="summary-card card">
          <div class="summary-label">{{ card.label }}</div>
          <div class="summary-value">{{ card.value }}</div>
        </div>
      </section>

      <section class="overview-grid">
        <div class="card">
          <div class="card-label">Current Shipment</div>
          <h2>{{ shipmentLabel }}</h2>
          <p class="muted">
            {{ simpleAppStore.shipment ? 'Shipment is configured and ready for route planning.' : 'Go to Dashboard to choose origin and destination.' }}
          </p>
        </div>

        <div class="card">
          <div class="card-label">Simulation Status</div>
          <h2>{{ simpleAppStore.simulation?.status || 'idle' }}</h2>
          <p class="muted">
            Phase: {{ simpleAppStore.simulation?.phase || 'idle' }}
          </p>
        </div>
      </section>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.page-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  align-items: flex-end;
}

.eyebrow {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-primary);
  margin-bottom: 0.5rem;
}

.hero h1 {
  margin: 0 0 0.75rem;
}

.hero-text,
.muted {
  color: var(--color-text-secondary);
}

.hero-actions,
.summary-grid,
.overview-grid {
  display: grid;
  gap: 1rem;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.overview-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.summary-label,
.card-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
}

.summary-value {
  font-size: 2rem;
  font-weight: 700;
}

@media (max-width: 900px) {
  .hero,
  .overview-grid,
  .summary-grid {
    grid-template-columns: 1fr;
    display: grid;
  }

  .hero-actions {
    justify-content: flex-start;
  }
}
</style>
