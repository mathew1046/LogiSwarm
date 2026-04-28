<script setup>
import { computed, onMounted } from 'vue'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'
import { useSimpleAppStore } from '@/stores/simpleApp'

const simpleAppStore = useSimpleAppStore()
const reports = computed(() => simpleAppStore.reports)

onMounted(async () => {
  await simpleAppStore.bootstrap()
  await simpleAppStore.fetchReports()
})
</script>

<template>
  <ProjectLayout>
    <div class="page-stack">
      <div class="page-header">
        <h1>Reports</h1>
        <p class="muted">Reports are generated when an active simulation is manually stopped.</p>
      </div>

      <div v-if="!reports.length" class="card muted">No reports yet.</div>

      <div v-else class="report-list">
        <div v-for="report in reports" :key="report.report_id" class="card report-card">
          <div class="card-label">{{ new Date(report.created_at).toLocaleString() }}</div>
          <h2>{{ report.title }}</h2>
          <p class="muted">Shipment: {{ report.shipment.origin_name }} → {{ report.shipment.destination_name }}</p>
          <p class="muted">Route: {{ report.route?.waypoints?.join(' → ') }}</p>
          <p class="muted">Simulation Status: {{ report.simulation.status }}</p>
        </div>
      </div>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.page-stack { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; flex-direction: column; gap: 0.35rem; }
.report-list { display: grid; gap: 1rem; }
.muted { color: var(--color-text-secondary); }
</style>
