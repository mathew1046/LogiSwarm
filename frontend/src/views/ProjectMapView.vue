<script setup>
import { onMounted } from 'vue'
import { useAgentStore } from '@/stores/agent'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'
import RiskMap from '@/components/map/RiskMap.vue'

const agentStore = useAgentStore()

onMounted(async () => {
  await agentStore.fetchRiskMap()
  agentStore.connectToSSE()
})
</script>

<template>
  <ProjectLayout>
    <div class="project-map-view">
      <RiskMap />
    </div>
  </ProjectLayout>
</template>

<style scoped>
.project-map-view {
  height: calc(100vh - var(--topbar-height));
  display: flex;
  flex-direction: column;
}
</style>
