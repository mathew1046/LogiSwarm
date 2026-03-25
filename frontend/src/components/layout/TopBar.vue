<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAlertStore } from '@/stores/alert'

const router = useRouter()
const projectStore = useProjectStore()
const alertStore = useAlertStore()

const currentProject = computed(() => projectStore.currentProject)
const unreadCount = computed(() => alertStore.unreadCount)

function goToProjects() {
  router.push('/projects')
}
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
      <button class="btn btn--secondary btn--sm" @click="alertStore.markAllAsRead" :disabled="unreadCount === 0">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount }}</span>
      </button>
    </div>
  </header>
</template>

<style scoped>
.notification-badge {
  background-color: var(--color-error);
  color: var(--color-text-inverse);
  font-size: var(--text-xs);
  padding: 2px 6px;
  border-radius: var(--radius-full);
  margin-left: var(--spacing-1);
}
</style>