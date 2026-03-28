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
defineProps({
  message: { type: String, default: 'Something went wrong' },
  retryable: { type: Boolean, default: true }
})

const emit = defineEmits(['retry'])
</script>

<template>
  <div class="error-state">
    <div class="error-icon">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M15 9l-6 6M9 9l6 6"/>
      </svg>
    </div>
    <h3 class="error-title">Error</h3>
    <p class="error-message">{{ message }}</p>
    <button 
      v-if="retryable"
      class="btn btn--primary"
      @click="emit('retry')"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M23 4v6h-6M1 20v-6h6"/>
        <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
      </svg>
      Try Again
    </button>
  </div>
</template>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  text-align: center;
}

.error-icon {
  color: var(--color-error);
  margin-bottom: var(--spacing-4);
}

.error-title {
  font-size: var(--text-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-2);
  color: var(--color-text);
}

.error-message {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-6);
  max-width: 400px;
}
</style>