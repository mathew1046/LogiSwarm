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
import { ref, computed, onMounted } from 'vue'

const TOUR_KEY = 'logiswarm_onboarding_completed'

const steps = [
  {
    id: 'welcome',
    title: 'Welcome to LogiSwarm',
    description: 'A geo-aware swarm of AI agents that monitors global supply chain routes and detects disruptions before they cascade.',
    target: null,
    position: 'center'
  },
  {
    id: 'create-project',
    title: 'Create a Project',
    description: 'Start by creating a new monitoring project. Select the regions you want to monitor and configure your thresholds.',
    target: '.project-create-btn',
    position: 'bottom'
  },
  {
    id: 'world-map',
    title: 'World Risk Map',
    description: 'View real-time risk levels across all monitored regions. Each colored polygon represents a geo-agent region with its current severity.',
    target: '.risk-map-container',
    position: 'top'
  },
  {
    id: 'agent-cards',
    title: 'Agent Status Cards',
    description: 'Each card shows a region\'s current risk level, confidence score, and last assessment. Click to expand for detailed reasoning.',
    target: '.agent-status-panel',
    position: 'top'
  },
  {
    id: 'disruption-feed',
    title: 'Disruption Event Feed',
    description: 'Real-time log of all detected disruption events. Filter by severity or region to focus on what matters.',
    target: '.event-feed-container',
    position: 'left'
  },
  {
    id: 'reports',
    title: 'Reports & Analysis',
    description: 'After a disruption resolves, generate detailed analysis reports. Chat with the Report Agent for follow-up questions.',
    target: '.report-viewer',
    position: 'left'
  },
  {
    id: 'complete',
    title: 'You\'re all set!',
    description: 'You\'re ready to start monitoring. Check the documentation for advanced features like agent interviews and scenario building.',
    target: null,
    position: 'center'
  }
]

const currentStep = ref(0)
const isActive = ref(false)
const hasCompleted = ref(false)

const currentStepData = computed(() => steps[currentStep.value])
const isFirstStep = computed(() => currentStep.value === 0)
const isLastStep = computed(() => currentStep.value === steps.length - 1)
const progress = computed(() => ((currentStep.value + 1) / steps.length) * 100)

onMounted(() => {
  const completed = localStorage.getItem(TOUR_KEY)
  hasCompleted.value = completed === 'true'
})

function startTour() {
  isActive.value = true
  currentStep.value = 0
}

function skipTour() {
  isActive.value = false
  localStorage.setItem(TOUR_KEY, 'true')
  hasCompleted.value = true
}

function nextStep() {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
  } else {
    completeTour()
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function goToStep(index) {
  if (index >= 0 && index < steps.length) {
    currentStep.value = index
  }
}

function completeTour() {
  isActive.value = false
  localStorage.setItem(TOUR_KEY, 'true')
  hasCompleted.value = true
}

function resetTour() {
  localStorage.removeItem(TOUR_KEY)
  hasCompleted.value = false
  startTour()
}

defineExpose({
  startTour,
  resetTour,
  hasCompleted
})
</script>

<template>
  <div v-if="isActive" class="tour-overlay" @click.self="skipTour">
    <div
      :class="['tour-step', `tour-step--${currentStepData.position}`]"
      @click.stop
    >
      <div class="tour-header">
        <h3>{{ currentStepData.title }}</h3>
        <button class="tour-close" @click="skipTour">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <p class="tour-description">{{ currentStepData.description }}</p>

      <div class="tour-progress">
        <div class="tour-progress-bar">
          <div class="tour-progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
        <span class="tour-step-counter">Step {{ currentStep + 1 }} of {{ steps.length }}</span>
      </div>

      <div class="tour-dots">
        <button
          v-for="(step, index) in steps"
          :key="step.id"
          :class="['tour-dot', { 'tour-dot--active': index === currentStep }]"
          @click="goToStep(index)"
        >
          <span class="sr-only">{{ step.title }}</span>
        </button>
      </div>

      <div class="tour-actions">
        <button v-if="!isFirstStep" class="btn btn--secondary btn--sm" @click="prevStep">
          Previous
        </button>
        <div class="tour-actions-spacer"></div>
        <button class="btn btn--ghost btn--sm" @click="skipTour">
          Skip Tour
        </button>
        <button class="btn btn--primary btn--sm" @click="nextStep">
          {{ isLastStep ? 'Finish' : 'Next' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tour-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.tour-step {
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  padding: var(--spacing-6);
  max-width: 400px;
  width: 90%;
}

.tour-step--center {
  margin: auto;
}

.tour-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-4);
}

.tour-header h3 {
  margin: 0;
  font-size: var(--text-lg);
}

.tour-close {
  background: none;
  border: none;
  padding: var(--spacing-1);
  cursor: pointer;
  color: var(--color-text-tertiary);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.tour-close:hover {
  background-color: var(--color-bg-secondary);
  color: var(--color-text);
}

.tour-description {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  margin: 0 0 var(--spacing-4);
}

.tour-progress {
  margin-bottom: var(--spacing-4);
}

.tour-progress-bar {
  height: 4px;
  background-color: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--spacing-2);
}

.tour-progress-fill {
  height: 100%;
  background-color: var(--color-primary);
  transition: width var(--transition-normal);
}

.tour-step-counter {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.tour-dots {
  display: flex;
  justify-content: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-4);
}

.tour-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--color-bg-tertiary);
  border: none;
  cursor: pointer;
  padding: 0;
  transition: all var(--transition-fast);
}

.tour-dot:hover {
  background-color: var(--color-text-tertiary);
}

.tour-dot--active {
  background-color: var(--color-primary);
  width: 20px;
  border-radius: var(--radius-full);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.tour-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.tour-actions-spacer {
  flex: 1;
}

.btn--ghost {
  background-color: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}

.btn--ghost:hover {
  background-color: var(--color-bg-secondary);
}
</style>