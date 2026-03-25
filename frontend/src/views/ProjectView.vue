<script setup>
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAgentStore } from '@/stores/agent'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'

const route = useRoute()
const projectStore = useProjectStore()
const agentStore = useAgentStore()

const currentProject = computed(() => projectStore.currentProject)

const steps = [
  { id: 'setup', label: 'Setup', icon: 'settings' },
  { id: 'monitoring', label: 'Monitoring', icon: 'eye' },
  { id: 'disruption', label: 'Disruption', icon: 'alert' },
  { id: 'response', label: 'Response', icon: 'action' },
  { id: 'report', label: 'Report', icon: 'document' }
]

onMounted(async () => {
  if (route.params.id) {
    await projectStore.fetchProject(route.params.id)
    await agentStore.fetchAgents()
  }
})
</script>

<template>
  <ProjectLayout>
    <div>
      <h1>{{ currentProject?.name || 'Project Dashboard' }}</h1>
      
      <div class="step-pills">
        <div v-for="step in steps" :key="step.id" class="step-pill">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
          </svg>
          <span>{{ step.label }}</span>
        </div>
      </div>
      
      <h2>Agent Status</h2>
      <div v-if="agentStore.loading" class="loading">
        <div class="loading__spinner"></div>
      </div>
      <div v-else class="grid grid--3">
        <div v-for="agent in agentStore.agents" :key="agent.region_id" class="card">
          <div class="card__header">
            <h3>{{ agent.region_name }}</h3>
            <span :class="['badge', `badge--${(agent.last_assessment?.severity || 'low').toLowerCase()}`]">
              {{ agent.last_assessment?.severity || 'LOW' }}
            </span>
          </div>
          <p>Confidence: {{ ((agent.last_assessment?.confidence || 0) * 100).toFixed(1) }}%</p>
          <p>Running: {{ agent.running ? 'Yes' : 'No' }}</p>
        </div>
      </div>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.step-pills {
  display: flex;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-6);
  padding-bottom: var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
  overflow-x: auto;
}

.step-pill {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background-color: var(--color-bg-secondary);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  white-space: nowrap;
}
</style>