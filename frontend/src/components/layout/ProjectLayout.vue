<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAgentStore } from '@/stores/agent'
import { useAlertStore } from '@/stores/alert'
import { useFeedStore } from '@/stores/feed'
import SidebarNav from './SidebarNav.vue'
import TopBar from './TopBar.vue'
import DegradationBanner from '@/components/feed/DegradationBanner.vue'

const route = useRoute()
const projectStore = useProjectStore()
const agentStore = useAgentStore()
const alertStore = useAlertStore()
const feedStore = useFeedStore()

onMounted(async () => {
  alertStore.initialize()
  
  if (route.params.id) {
    await projectStore.fetchProject(route.params.id)
  }
  
  agentStore.connectToSSE()
  await feedStore.fetchDegradationStatus()
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
      <DegradationBanner />
      <main class="app-layout__content">
        <slot />
      </main>
    </div>
  </div>
</template>