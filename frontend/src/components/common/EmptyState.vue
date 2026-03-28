<!--
LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
Copyright (C) 2025 LogiSwarm Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
-->

<script setup>
defineProps({
  icon: { type: String, default: 'check' },
  title: { type: String, default: 'No data' },
  message: { type: String, default: 'No items to display' }
})
</script>

<template>
  <div class="empty-state">
    <div class="empty-icon">
      <svg v-if="icon === 'check'" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 11-5.17-8.77"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
      <svg v-else-if="icon === 'inbox'" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/>
        <path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z"/>
      </svg>
      <svg v-else width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
        <line x1="9" y1="9" x2="9.01" y2="9"/>
        <line x1="15" y1="9" x2="15.01" y2="9"/>
      </svg>
    </div>
    <h3 class="empty-title">{{ title }}</h3>
    <p class="empty-message">{{ message }}</p>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  text-align: center;
}

.empty-icon {
  color: var(--color-success);
  margin-bottom: var(--spacing-4);
}

.empty-title {
  font-size: var(--text-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-2);
  color: var(--color-text);
}

.empty-message {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  max-width: 400px;
}
</style>