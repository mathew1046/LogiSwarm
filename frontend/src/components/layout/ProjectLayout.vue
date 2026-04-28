<script setup>
import { onMounted } from 'vue'
import { useSimpleAppStore } from '@/stores/simpleApp'
import SidebarNav from './SidebarNav.vue'
import TopBar from './TopBar.vue'

const simpleAppStore = useSimpleAppStore()

onMounted(async () => {
  if (!simpleAppStore.places.length) {
    await simpleAppStore.bootstrap()
  }
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

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background-color: var(--color-bg);
}

.app-layout__main {
  flex: 1;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-layout__content {
  flex: 1;
  padding: var(--spacing-6);
  overflow-y: auto;
  background-color: var(--color-bg);
}
</style>
