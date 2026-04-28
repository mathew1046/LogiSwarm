<script setup>
import { computed } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { useSimpleAppStore } from '@/stores/simpleApp'

const themeStore = useThemeStore()
const simpleAppStore = useSimpleAppStore()

const shipmentLabel = computed(() => {
  if (!simpleAppStore.shipment) return 'No shipment selected'
  return `${simpleAppStore.shipment.origin_name} → ${simpleAppStore.shipment.destination_name}`
})
</script>

<template>
  <header class="app-layout__topbar glass">
    <div class="topbar-left">
      <div class="project-selector">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 7h16M4 12h16M4 17h16" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>{{ shipmentLabel }}</span>
      </div>
    </div>

    <div class="topbar-right">
      <button
        class="btn btn--ghost btn--sm theme-toggle"
        @click="themeStore.cycleTheme"
        :title="`Theme: ${themeStore.preference}`"
      >
        Theme
      </button>
    </div>
  </header>
</template>

<style scoped>
.theme-toggle {
  padding: var(--spacing-2) var(--spacing-3);
}
</style>
