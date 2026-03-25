<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAgentStore } from '@/stores/agent'
import { useAlertStore } from '@/stores/alert'
import SidebarNav from './SidebarNav.vue'
import TopBar from './TopBar.vue'

const route = useRoute()
const projectStore = useProjectStore()
const agentStore = useAgentStore()
const alertStore = useAlertStore()

onMounted(async () => {
  alertStore.initialize()
  
  if (route.params.id) {
    await projectStore.fetchProject(route.params.id)
  }
  
  agentStore.connectToSSE()
})

onUnmounted(() => {
  agentStore.disconnectSSE()
})
</script>

<template>
  <div class="app-layout">
    <SidebarNav />
    <div class="app-layout__main">
      <TopBar />
      <main class="app-layout__content">
        <slot />
      </main>
    </div>
  </div>
</template>