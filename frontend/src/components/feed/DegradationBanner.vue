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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useFeedStore } from '@/stores/feed'

const feedStore = useFeedStore()
const expanded = ref(false)
const refreshInterval = ref(null)

const isAnyDegraded = computed(() => feedStore.isAnyDegraded)
const degradedRegions = computed(() => feedStore.degradedRegions)
const offlineRegions = computed(() => feedStore.offlineRegions)
const loading = computed(() => feedStore.loading)

const latestOfflineRegion = computed(() => {
  if (offlineRegions.value.length === 0) return null
  return offlineRegions.value[0]
})

const otherDegradedCount = computed(() => {
  return Math.max(0, degradedRegions.value.length - 1)
})

function formatAge(minutes) {
  if (minutes === null || minutes === undefined) return 'unknown'
  if (minutes < 60) return `${Math.round(minutes)}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  return `${days}d ago`
}

function toggleExpanded() {
  expanded.value = !expanded.value
}

onMounted(async () => {
  await feedStore.fetchDegradationStatus()
  refreshInterval.value = setInterval(() => {
    feedStore.fetchDegradationStatus()
  }, 60000)
})

onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
})
</script>

<template>
  <div v-if="isAnyDegraded" class="degradation-banner" :class="{ 'degradation-banner--offline': offlineRegions.length > 0 }">
    <div class="degradation-banner__header" @click="toggleExpanded">
      <div class="degradation-banner__icon">
        <svg v-if="offlineRegions.length > 0" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      </div>
      <div class="degradation-banner__message">
        <template v-if="latestOfflineRegion">
          <strong>Feed unavailable</strong> — 
          {{ latestOfflineRegion.region_name }}: using cached data from {{ formatAge(latestOfflineRegion.cached_data_age_minutes) }}
          <span v-if="otherDegradedCount > 0">(+{{ otherDegradedCount }} other{{ otherDegradedCount > 1 ? 's' : '' }})</span>
        </template>
        <template v-else>
          <strong>Degraded feed</strong> — 
          {{ degradedRegions.length }} region{{ degradedRegions.length > 1 ? 's' : '' }} operating with reduced data quality
        </template>
      </div>
      <div class="degradation-banner__expand">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'rotate': expanded }">
          <path d="M19 9l-7 7-7-7"/>
        </svg>
      </div>
    </div>

    <div v-if="expanded" class="degradation-banner__details">
      <div v-for="region in degradedRegions" :key="region.region_id" class="degraded-region">
        <div class="degraded-region__header">
          <span class="degraded-region__name">{{ region.region_name }}</span>
          <span class="degraded-region__mode" :class="`mode--${region.mode.toLowerCase()}`">
            {{ region.mode }}
          </span>
        </div>
        <div class="degraded-region__info">
          <span v-if="region.cached_data_age_minutes !== null">
            Cached data age: {{ formatAge(region.cached_data_age_minutes) }}
          </span>
          <span v-if="region.uncertainty_factor > 0">
            Confidence reduced: {{ (region.uncertainty_factor * 100).toFixed(0) }}%
          </span>
        </div>
        <div v-if="region.degraded_connectors.length > 0" class="degraded-region__connectors">
          Unavailable: {{ region.degraded_connectors.join(', ') }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.degradation-banner {
  background-color: var(--color-warning-bg, #fef3c7);
  border-bottom: 1px solid var(--color-warning-border, #fcd34d);
  padding: var(--spacing-3) var(--spacing-4);
}

.degradation-banner--offline {
  background-color: var(--color-error-bg, #fee2e2);
  border-bottom-color: var(--color-error-border, #fca5a5);
}

.degradation-banner__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  cursor: pointer;
}

.degradation-banner__icon {
  color: var(--color-warning, #d97706);
  flex-shrink: 0;
}

.degradation-banner--offline .degradation-banner__icon {
  color: var(--color-error, #dc2626);
}

.degradation-banner__message {
  flex: 1;
  font-size: var(--text-sm);
  color: var(--color-text);
}

.degradation-banner__expand {
  color: var(--color-text-secondary);
  transition: transform var(--transition-fast);
}

.degradation-banner__expand svg.rotate {
  transform: rotate(180deg);
}

.degradation-banner__details {
  margin-top: var(--spacing-3);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.degraded-region {
  padding: var(--spacing-2);
  background-color: var(--color-bg);
  border-radius: var(--radius-sm);
}

.degraded-region__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-1);
}

.degraded-region__name {
  font-weight: 600;
  font-size: var(--text-sm);
}

.degraded-region__mode {
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
}

.mode--degraded {
  background-color: var(--color-warning-bg, #fef3c7);
  color: var(--color-warning, #d97706);
}

.mode--offline {
  background-color: var(--color-error-bg, #fee2e2);
  color: var(--color-error, #dc2626);
}

.degraded-region__info {
  display: flex;
  gap: var(--spacing-4);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.degraded-region__connectors {
  margin-top: var(--spacing-1);
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}
</style>