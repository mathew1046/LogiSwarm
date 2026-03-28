// LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
// Copyright (C) 2025 LogiSwarm Contributors
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

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