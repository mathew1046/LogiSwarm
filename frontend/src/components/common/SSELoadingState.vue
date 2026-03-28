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
  message: { type: String, default: 'Connecting to live feed...' }
})
</script>

<template>
  <div class="sse-loading">
    <div class="sse-loading__dots">
      <span></span>
      <span></span>
      <span></span>
    </div>
    <p class="sse-loading__message">{{ message }}</p>
  </div>
</template>

<style scoped>
.sse-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
  text-align: center;
}

.sse-loading__dots {
  display: flex;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
}

.sse-loading__dots span {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-full);
  background-color: var(--color-primary);
  animation: bounce 1.4s ease-in-out infinite both;
}

.sse-loading__dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.sse-loading__dots span:nth-child(2) {
  animation-delay: -0.16s;
}

.sse-loading__message {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>