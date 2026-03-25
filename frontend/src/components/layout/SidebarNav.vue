<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAlertStore } from '@/stores/alert'

const route = useRoute()
const projectStore = useProjectStore()
const alertStore = useAlertStore()

const currentProjectName = computed(() => projectStore.currentProject?.name || 'Select Project')
const unreadAlerts = computed(() => alertStore.unreadCount)

const navSections = [
  {
    title: 'Overview',
    items: [
      { path: '/', label: 'Home', icon: 'home' },
      { path: '/projects', label: 'Projects', icon: 'folder' },
      { path: '/history', label: 'History', icon: 'history' }
    ]
  },
  {
    title: 'Project',
    items: [
      { path: '/projects/:id', label: 'Dashboard', icon: 'dashboard', requiresProject: true },
      { path: '/projects/:id/map', label: 'Risk Map', icon: 'map', requiresProject: true },
      { path: '/projects/:id/reports', label: 'Reports', icon: 'reports', requiresProject: true },
      { path: '/projects/:id/interact', label: 'Interact', icon: 'chat', requiresProject: true }
    ]
  }
]

function isActive(itemPath) {
  if (itemPath.includes(':id')) {
    const pattern = itemPath.replace(':id', '[^/]+')
    const regex = new RegExp(`^${pattern}$`)
    return regex.test(route.path)
  }
  return route.path === itemPath
}

function getActualPath(itemPath) {
  if (itemPath.includes(':id') && projectStore.currentProject) {
    return itemPath.replace(':id', projectStore.currentProject.id)
  }
  return itemPath
}

const iconPaths = {
  home: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
  folder: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z',
  history: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
  dashboard: 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z',
  map: 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7',
  reports: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  chat: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z'
}
</script>

<template>
  <aside class="app-layout__sidebar">
    <div class="sidebar-logo">
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
        <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="2"/>
        <circle cx="16" cy="16" r="6" fill="currentColor"/>
        <path d="M16 2v6M16 24v6M2 16h6M24 16h6" stroke="currentColor" stroke-width="2"/>
      </svg>
      <span class="sidebar-logo__text">LogiSwarm</span>
    </div>
    
    <nav class="sidebar-nav">
      <div v-for="section in navSections" :key="section.title" class="sidebar-section">
        <div class="sidebar-section__title">{{ section.title }}</div>
        <router-link
          v-for="item in section.items"
          :key="item.path"
          :to="getActualPath(item.path)"
          :class="['sidebar-link', { 'sidebar-link--active': isActive(item.path) }]"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path :d="iconPaths[item.icon]" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          {{ item.label }}
        </router-link>
      </div>
    </nav>
    
    <div class="sidebar-version">
      <span class="version-badge">v0.1.0</span>
    </div>
  </aside>
</template>

<style scoped>
.sidebar-version {
  position: absolute;
  bottom: var(--spacing-4);
  left: 0;
  right: 0;
  padding: var(--spacing-4);
  text-align: center;
}
</style>