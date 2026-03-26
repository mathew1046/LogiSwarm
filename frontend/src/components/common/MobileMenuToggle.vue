<script setup>
import { ref } from 'vue'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()
const sidebarOpen = ref(false)

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
  document.querySelector('.app-layout__sidebar')?.classList.toggle('app-layout__sidebar--open', sidebarOpen.value)
}

function getThemeIcon() {
  if (themeStore.preference === themeStore.THEMES.SYSTEM) {
    return 'system'
  }
  return themeStore.preference === themeStore.THEMES.DARK ? 'dark' : 'light'
}
</script>

<template>
  <button class="btn btn--secondary btn--sm mobile-menu-toggle" @click="toggleSidebar">
    <svg v-if="!sidebarOpen" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M3 12h18M3 6h18M3 18h18"/>
    </svg>
    <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M18 6L6 18M6 6l12 12"/>
    </svg>
  </button>
</template>

<style scoped>
.mobile-menu-toggle {
  display: none;
}

@media (max-width: 768px) {
  .mobile-menu-toggle {
    display: inline-flex;
  }
}
</style>