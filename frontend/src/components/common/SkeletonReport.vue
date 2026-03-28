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
</script>

<template>
  <div class="skeleton-report">
    <div class="skeleton-report__header">
      <div class="skeleton-line skeleton-line--xl"></div>
      <div class="skeleton-line skeleton-line--md"></div>
    </div>
    <div class="skeleton-report__content">
      <div class="skeleton-line"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line skeleton-line--lg"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line skeleton-line--md"></div>
    </div>
    <div class="skeleton-report__sidebar">
      <div class="suggestion-skeleton"></div>
      <div class="suggestion-skeleton"></div>
      <div class="suggestion-skeleton"></div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-report {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: var(--spacing-6);
}

.skeleton-report__header {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-4);
}

.skeleton-report__content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.skeleton-report__sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.skeleton-line {
  height: 16px;
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

.skeleton-line--md {
  width: 70%;
}

.skeleton-line--lg {
  width: 85%;
}

.skeleton-line--xl {
  width: 95%;
  height: 32px;
}

.suggestion-skeleton {
  height: 60px;
  background: linear-gradient(
    90deg,
    var(--color-bg-tertiary) 25%,
    var(--color-bg-secondary) 50%,
    var(--color-bg-tertiary) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-md);
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