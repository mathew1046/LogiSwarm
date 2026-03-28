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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAlertStore } from '@/stores/alert'
import { useThemeStore } from '@/stores/theme'
import OnboardingTour from '@/components/common/OnboardingTour.vue'

const router = useRouter()
const projectStore = useProjectStore()
const alertStore = useAlertStore()
const themeStore = useThemeStore()

const currentProject = computed(() => projectStore.currentProject)
const unreadCount = computed(() => alertStore.unreadCount)
const isDark = computed(() => themeStore.isDark())

const tourRef = ref(null)
const showTourButton = ref(false)

function goToProjects() {
  router.push('/projects')
}

function getThemeIcon() {
  if (themeStore.preference === themeStore.THEMES.SYSTEM) {
    return 'system'
  }
  return themeStore.preference === themeStore.THEMES.DARK ? 'dark' : 'light'
}

function startTour() {
  if (tourRef.value) {
    tourRef.value.startTour()
  }
}

onMounted(() => {
  const completed = localStorage.getItem('logiswarm_onboarding_completed')
  showTourButton.value = completed === 'true'
})
</script>

<template>
  <header class="app-layout__topbar">
    <div class="topbar-left">
      <div v-if="currentProject" class="project-selector" @click="goToProjects">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>{{ currentProject.name }}</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 9l-7 7-7-7" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div v-else class="project-selector" @click="goToProjects">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 4v16m8-8H4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>New Project</span>
      </div>
    </div>
    
    <div class="topbar-right">
      <button 
        v-if="showTourButton"
        class="btn btn--ghost btn--sm tour-btn"
        @click="startTour"
        title="Take a tour"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/>
          <path d="M12 17h.01"/>
        </svg>
      </button>
      
      <button 
        class="btn btn--secondary btn--sm theme-toggle" 
        @click="themeStore.cycleTheme"
        :title="`Theme: ${themeStore.preference}`"
      >
        <svg v-if="getThemeIcon() === 'light'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="5"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>
        <svg v-else-if="getThemeIcon() === 'dark'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
        </svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
          <path d="M8 21h8M12 17v4"/>
        </svg>
      </button>
      
      <button class="btn btn--secondary btn--sm" @click="alertStore.markAllAsRead" :disabled="unreadCount === 0">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount }}</span>
      </button>
    </div>
    
    <OnboardingTour ref="tourRef" />
  </header>
</template>

<style scoped>
.tour-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2);
  min-width: 36px;
}

.theme-toggle {
  padding: var(--spacing-2);
  min-width: 36px;
}

.notification-badge {
  background-color: var(--color-error);
  color: var(--color-text-inverse);
  font-size: var(--text-xs);
  padding: 2px 6px;
  border-radius: var(--radius-full);
  margin-left: var(--spacing-1);
}

.notification-badge:empty {
  display: none;
}
</style>