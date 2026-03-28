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
import { computed } from 'vue'

const props = defineProps({
  steps: {
    type: Array,
    required: true,
    validator: (steps) => steps.every(s => 'id' in s && 'label' in s)
  },
  activeStep: {
    type: String,
    required: true
  },
  completedSteps: {
    type: Array,
    default: () => []
  }
})

const stepIndex = computed(() => {
  return props.steps.findIndex(s => s.id === props.activeStep)
})

function getStepStatus(stepId) {
  if (props.completedSteps.includes(stepId)) {
    return 'completed'
  }
  if (props.steps.findIndex(s => s.id === stepId) === stepIndex.value) {
    return 'active'
  }
  return 'pending'
}
</script>

<template>
  <div class="step-workflow">
    <div class="step-pills">
      <template v-for="(step, index) in steps" :key="step.id">
        <div 
          :class="['step-pill', getStepStatus(step.id)]"
          :title="step.label"
        >
          <div class="step-pill__icon">
            <svg v-if="getStepStatus(step.id) === 'completed'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <path d="M20 6L9 17l-5-5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <span class="step-pill__label">{{ step.label }}</span>
        </div>
        <div v-if="index < steps.length - 1" class="step-connector">
          <div class="step-connector__line" :class="{ completed: getStepStatus(steps[index + 1].id) !== 'pending' }"></div>
        </div>
      </template>
    </div>
    <div class="step-content">
      <slot></slot>
    </div>
  </div>
</template>

<style scoped>
.step-workflow {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.step-pills {
  display: flex;
  align-items: center;
  padding: var(--spacing-4);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  overflow-x: auto;
  flex-shrink: 0;
}

.step-pill {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-full);
  background-color: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.step-pill.active {
  background-color: var(--color-primary);
  color: var(--color-text-inverse);
}

.step-pill.completed {
  background-color: var(--color-success);
  color: var(--color-text-inverse);
}

.step-pill__icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  background-color: rgba(255, 255, 255, 0.2);
  font-size: var(--text-xs);
  font-weight: 600;
}

.step-pill__label {
  font-size: var(--text-sm);
  font-weight: 500;
}

.step-connector {
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-2);
}

.step-connector__line {
  width: 24px;
  height: 2px;
  background-color: var(--color-border);
  transition: background-color var(--transition-fast);
}

.step-connector__line.completed {
  background-color: var(--color-success);
}

.step-content {
  flex: 1;
  overflow-y: auto;
}
</style>