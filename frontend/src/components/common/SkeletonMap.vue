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
  showMap: { type: Boolean, default: true }
})
</script>

<template>
  <div class="skeleton-map">
    <div v-if="showMap" class="skeleton-map__canvas">
      <div class="skeleton-map__regions">
        <div class="region-skeleton region-skeleton--1"></div>
        <div class="region-skeleton region-skeleton--2"></div>
        <div class="region-skeleton region-skeleton--3"></div>
        <div class="region-skeleton region-skeleton--4"></div>
      </div>
    </div>
    <div class="skeleton-map__overlay">
      <div class="overlay-item"></div>
      <div class="overlay-item"></div>
      <div class="overlay-item"></div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-map {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.skeleton-map__canvas {
  width: 100%;
  height: 400px;
  background: linear-gradient(
    135deg,
    var(--color-bg-tertiary) 0%,
    var(--color-bg-secondary) 50%,
    var(--color-bg-tertiary) 100%
  );
  border-radius: var(--radius-lg);
  position: relative;
  overflow: hidden;
  animation: pulse 2s ease-in-out infinite;
}

.skeleton-map__regions {
  position: absolute;
  inset: 0;
}

.region-skeleton {
  position: absolute;
  background: rgba(59, 130, 246, 0.1);
  border: 2px solid rgba(59, 130, 246, 0.2);
  border-radius: var(--radius-md);
  animation: fade 2s ease-in-out infinite;
}

.region-skeleton--1 {
  top: 30%;
  left: 10%;
  width: 25%;
  height: 20%;
}

.region-skeleton--2 {
  top: 15%;
  left: 45%;
  width: 20%;
  height: 25%;
}

.region-skeleton--3 {
  top: 50%;
  left: 25%;
  width: 30%;
  height: 15%;
}

.region-skeleton--4 {
  top: 20%;
  left: 70%;
  width: 22%;
  height: 30%;
}

.skeleton-map__overlay {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  padding: var(--spacing-4);
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.overlay-item {
  height: 24px;
  background: linear-gradient(
    90deg,
    var(--color-bg-tertiary) 25%,
    var(--color-bg-secondary) 50%,
    var(--color-bg-tertiary) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-sm);
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

@keyframes fade {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.5;
  }
}
</style>