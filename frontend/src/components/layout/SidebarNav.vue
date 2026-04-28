<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navItems = [
  { path: '/', label: 'Home', icon: 'home' },
  { path: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { path: '/agents', label: 'Agents', icon: 'agents' },
  { path: '/simulation', label: 'Simulation', icon: 'lab' },
  { path: '/reports', label: 'Reports', icon: 'reports' },
  { path: '/routes', label: 'Routes', icon: 'routes' }
]

function isActive(itemPath) {
  return route.path === itemPath
}

function handleLogin() {
  router.push('/login')
}

function handleLogout() {
  authStore.logout()
  router.push('/')
}

const iconPaths = {
  home: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
  dashboard: 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z',
  agents: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
  lab: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z',
  reports: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  routes: 'M13 17h8m0 0V9m0 8l-8-8-4 4-6-6'
}
</script>

<template>
  <aside class="app-layout__sidebar">
    <div class="sidebar-logo">
      <svg class="sidebar-logo__icon" width="28" height="28" viewBox="0 0 32 32" fill="none">
        <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="2"/>
        <circle cx="16" cy="16" r="6" fill="currentColor"/>
        <path d="M16 2v6M16 24v6M2 16h6M24 16h6" stroke="currentColor" stroke-width="2"/>
      </svg>
      <span class="sidebar-logo__text">LogiSwarm</span>
    </div>

    <nav class="sidebar-nav simple-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        :class="['sidebar-link', { 'sidebar-link--active': isActive(item.path) }]"
      >
        <svg class="sidebar-link__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path :d="iconPaths[item.icon]" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ item.label }}
      </router-link>
    </nav>

    <div class="sidebar-auth">
      <div v-if="authStore.isAuthenticated" class="auth-info">
        <div class="auth-user">{{ authStore.displayName }}</div>
        <button class="btn btn--secondary btn--sm" @click="handleLogout">Sign Out</button>
      </div>
      <button v-else class="btn btn--primary btn--sm btn--full" @click="handleLogin">Sign In</button>
    </div>
  </aside>
</template>

<style scoped>
.simple-nav {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.sidebar-auth {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: var(--spacing-4);
  border-top: 1px solid var(--color-border);
}

.sidebar-auth .auth-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  align-items: center;
}

.auth-user {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
  text-align: center;
}

.btn--sm {
  padding: var(--spacing-1) var(--spacing-3);
  font-size: var(--text-xs);
}

.btn--full {
  width: 100%;
  justify-content: center;
}
</style>
