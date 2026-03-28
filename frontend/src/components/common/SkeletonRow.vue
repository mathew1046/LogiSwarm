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
</script>

<template>
  <div class="skeleton-row">
    <div class="skeleton-cell skeleton-cell--sm"></div>
    <div class="skeleton-cell skeleton-cell--lg"></div>
    <div class="skeleton-cell skeleton-cell--md"></div>
    <div class="skeleton-cell skeleton-cell--md"></div>
    <div class="skeleton-cell skeleton-cell--sm"></div>
  </div>
</template>

<style scoped>
.skeleton-row {
  display: grid;
  grid-template-columns: 1fr 2fr 1.5fr 1.5fr 1fr;
  gap: var(--spacing-4);
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
}

.skeleton-cell {
  height: 20px;
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

.skeleton-cell--sm {
  width: 60%;
}

.skeleton-cell--md {
  width: 80%;
}

.skeleton-cell--lg {
  width: 90%;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>