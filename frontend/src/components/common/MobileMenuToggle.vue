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