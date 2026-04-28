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
            <svg v-if="getStepStatus(step.id) === 'completed'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
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
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  overflow-x: auto;
  flex-shrink: 0;
}

.step-pill {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-md);
  background-color: var(--color-bg-tertiary);
  color: var(--color-text-tertiary);
  transition: all var(--transition-fast);
  white-space: nowrap;
  border: 1px solid transparent;
}

.step-pill.active {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  color: var(--color-text-inverse);
  box-shadow: var(--shadow-primary);
}

.step-pill.completed {
  background-color: var(--color-success);
  color: var(--color-text-inverse);
}

.step-pill__icon {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  background-color: rgba(255, 255, 255, 0.15);
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
  padding: 0 var(--spacing-1);
}

.step-connector__line {
  width: 20px;
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
