<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAgentStore } from '@/stores/agent'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'
import StepWorkflow from '@/components/common/StepWorkflow.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const agentStore = useAgentStore()

const activeStep = ref('setup')
const completedSteps = ref(['setup'])
const isLoading = ref(true)
const error = ref(null)

const steps = [
  { id: 'setup', label: 'Setup' },
  { id: 'monitoring', label: 'Monitoring' },
  { id: 'disruption', label: 'Disruption' },
  { id: 'response', label: 'Response' },
  { id: 'report', label: 'Report' }
]

const currentProject = computed(() => projectStore.currentProject)
const agents = computed(() => agentStore.agents)
const highRiskAgents = computed(() => agentStore.highRiskAgents)

function getSeverityClass(severity) {
  const s = (severity || 'low').toLowerCase()
  return `badge--${s}`
}

function getSeverityColor(severity) {
  const colors = {
    low: 'var(--color-low)',
    medium: 'var(--color-medium)',
    high: 'var(--color-high)',
    critical: 'var(--color-critical)'
  }
  return colors[(severity || 'low').toLowerCase()] || colors.low
}

function getRiskCardClass(severity) {
  return `risk-${(severity || 'low').toLowerCase()}`
}

function formatDate(date) {
  return new Date(date).toLocaleString()
}

function getConfidencePercent(confidence) {
  return ((confidence || 0) * 100).toFixed(1)
}

onMounted(async () => {
  if (route.params.id) {
    try {
      isLoading.value = true
      error.value = null
      await projectStore.fetchProject(route.params.id)
      await agentStore.fetchAgents()
    } catch (err) {
      error.value = err.message || 'Failed to load project'
    } finally {
      isLoading.value = false
    }
  }
})

function goToStep(stepId) {
  const currentIndex = steps.findIndex(s => s.id === activeStep.value)
  const targetIndex = steps.findIndex(s => s.id === stepId)

  // Allow navigation if stepping backward, or if step was already completed, or if it's the next uncompleted step
  if (targetIndex <= currentIndex || completedSteps.value.includes(stepId)) {
    activeStep.value = stepId
    // Mark as completed when visiting
    if (!completedSteps.value.includes(stepId)) {
      completedSteps.value.push(stepId)
    }
  }
}

function nextStep() {
  const currentIndex = steps.findIndex(s => s.id === activeStep.value)
  if (currentIndex < steps.length - 1) {
    const nextStepId = steps[currentIndex + 1].id
    activeStep.value = nextStepId
    if (!completedSteps.value.includes(nextStepId)) {
      completedSteps.value.push(nextStepId)
    }
  }
}

function prevStep() {
  const currentIndex = steps.findIndex(s => s.id === activeStep.value)
  if (currentIndex > 0) {
    activeStep.value = steps[currentIndex - 1].id
  }
}

function startMonitoring() {
  nextStep()
}

function runSimulation() {
  router.push('/simulation')
}

function goToMap() {
  router.push(`/projects/${route.params.id}/map`)
}

function goToReports() {
  router.push(`/projects/${route.params.id}/reports`)
}
</script>

<template>
  <ProjectLayout>
    <div class="project-view">
      <header class="project-header">
        <div class="project-header__title">
          <h1>{{ currentProject?.name || 'Project Dashboard' }}</h1>
          <span v-if="currentProject" :class="['badge', getSeverityClass(currentProject?.status)]">
            {{ currentProject?.status || 'idle' }}
          </span>
        </div>
        <div class="project-header__actions">
          <button class="btn btn--secondary btn--sm" @click="goToMap">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Risk Map
          </button>
          <button class="btn btn--secondary btn--sm" @click="goToReports">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Reports
          </button>
        </div>
      </header>

      <div v-if="isLoading" class="loading-state">
        <div class="loading__spinner"></div>
        <p>Loading project...</p>
      </div>

      <div v-else-if="error" class="error-state">
        <div class="error-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <p class="error-state__title">Failed to Load Project</p>
        <p class="error-state__text">{{ error }}</p>
        <button class="btn btn--primary" @click="router.push('/projects')">
          Back to Projects
        </button>
      </div>

      <StepWorkflow
        :steps="steps"
        :active-step="activeStep"
        :completed-steps="completedSteps"
      >
        <div class="step-panel">
          <div v-if="activeStep === 'setup'" class="step-section">
            <h2>Setup</h2>
            <p class="text-secondary">Configure your monitoring regions and thresholds.</p>

            <div class="setup-summary card card--glass">
              <h3>Configuration</h3>
              <div class="config-grid">
                <div class="config-item">
                  <span class="config-label">Monitored Regions</span>
                  <span class="config-value text-mono">{{ currentProject?.config?.regions?.length || 0 }} regions</span>
                </div>
                <div class="config-item">
                  <span class="config-label">Average Threshold</span>
                  <span class="config-value text-mono">
                    {{ currentProject?.config?.thresholds ?
                      (Object.values(currentProject.config.thresholds).reduce((a, b) => a + b, 0) / Object.keys(currentProject.config.thresholds).length).toFixed(2) :
                      '0.75' }}
                  </span>
                </div>
              </div>
              <div class="setup-actions">
                <button class="btn btn--primary" @click="startMonitoring">
                  Start Monitoring
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M13 7l5 5m0 0l-5 5m5-5H6" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <div v-else-if="activeStep === 'monitoring'" class="step-section">
            <h2>Agent Monitoring</h2>
            <p class="text-secondary">Live status of all geo-agents monitoring your supply chain.</p>

            <div v-if="agentStore.loading" class="loading">
              <div class="loading__spinner"></div>
            </div>

            <div v-else>
              <div class="monitoring-actions">
                <button class="btn btn--primary" @click="runSimulation">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  Run Simulation
                </button>
              </div>

              <div class="agents-grid">
                <div
                  v-for="agent in agents"
                  :key="agent.region_id"
                  :class="['agent-card', 'card', 'card--glass', getRiskCardClass(agent.last_assessment?.severity)]"
                >
                  <div class="agent-card__header">
                    <h3>{{ agent.region_name }}</h3>
                    <span :class="['badge', getSeverityClass(agent.last_assessment?.severity)]">
                      {{ agent.last_assessment?.severity || 'LOW' }}
                    </span>
                  </div>
                  <div class="agent-card__stats">
                    <div class="stat">
                      <span class="stat__label">Confidence</span>
                      <span class="stat__value text-mono">
                        {{ getConfidencePercent(agent.last_assessment?.confidence) }}%
                      </span>
                    </div>
                    <div class="stat">
                      <span class="stat__label">Status</span>
                      <span class="stat__value">
                        <span :class="['status-dot', { 'status-dot--active': agent.running }]"></span>
                        {{ agent.running ? 'Running' : 'Stopped' }}
                      </span>
                    </div>
                  </div>
                  <div class="agent-card__reasoning" v-if="agent.last_assessment?.reasoning">
                    <p>{{ agent.last_assessment.reasoning }}</p>
                  </div>
                  <div class="agent-card__time text-mono">
                    Last cycle: {{ agent.last_cycle_at ? formatDate(agent.last_cycle_at) : 'Never' }}
                  </div>
                </div>
</div>
          </div>
          </div>

          <div v-else-if="activeStep === 'disruption'" class="step-section">
            <h2>Active Disruptions</h2>
            <p class="text-secondary">Current disruptions detected across your monitored regions.</p>

            <div v-if="highRiskAgents.length === 0" class="empty-state">
              <div class="success-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <p class="empty-state__title">No Active Disruptions</p>
              <p class="empty-state__text">All regions are operating normally. No disruptions have been detected.</p>
            </div>

            <div v-else class="disruptions-list">
              <div
                v-for="agent in highRiskAgents"
                :key="agent.region_id"
                :class="['disruption-card', 'card', 'card--glass', getRiskCardClass(agent.last_assessment?.severity)]"
              >
                <div class="disruption-header">
                  <h3>{{ agent.region_name }}</h3>
                  <span :class="['badge', getSeverityClass(agent.last_assessment?.severity)]">
                    {{ agent.last_assessment?.severity }}
                  </span>
                </div>
                <p class="disruption-reasoning">{{ agent.last_assessment?.reasoning }}</p>
                <div class="disruption-actions">
                  <h4>Recommended Actions:</h4>
                  <ul>
                    <li v-for="action in (agent.last_assessment?.recommended_actions || [])" :key="action">
                      {{ action }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeStep === 'response'" class="step-section">
            <h2>Response Actions</h2>
            <p class="text-secondary">Recommended and automated responses to detected disruptions.</p>

            <div class="response-grid">
              <div class="response-card card card--glass">
                <h3>Pending Actions</h3>
                <div class="empty-state">
                  <p class="text-secondary">No pending actions at this time.</p>
                </div>
              </div>
              <div class="response-card card card--glass">
                <h3>Completed Actions</h3>
                <div class="empty-state">
                  <p class="text-secondary">No completed actions yet.</p>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeStep === 'report'" class="step-section">
            <h2>Reports</h2>
            <p class="text-secondary">Post-disruption analysis reports and insights.</p>

            <div class="reports-placeholder card card--glass">
              <button class="btn btn--primary" @click="goToReports">
                View All Reports
              </button>
            </div>
          </div>
        </div>
      </StepWorkflow>

      <div v-if="!isLoading && !error" class="step-navigation">
        <button
          class="btn btn--secondary"
          :disabled="steps.findIndex(s => s.id === activeStep) === 0"
          @click="prevStep"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 7l-5 5m0 0l5 5m-5-5h12" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Previous
        </button>
        <button
          v-if="steps.findIndex(s => s.id === activeStep) < steps.length - 1"
          class="btn btn--primary"
          @click="nextStep"
        >
          Next
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M13 7l5 5m0 0l-5 5m5-5H6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.project-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-6);
}

.project-header__title {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.project-header__title h1 {
  margin: 0;
  font-size: var(--text-2xl);
  font-weight: 600;
}

.project-header__actions {
  display: flex;
  gap: var(--spacing-2);
}

.step-section {
  padding: var(--spacing-6) 0;
}

.step-section h2 {
  margin-bottom: var(--spacing-2);
  font-size: var(--text-xl);
  font-weight: 600;
}

.text-secondary {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-6);
}

.setup-summary {
  background: var(--color-bg-secondary);
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-4);
  margin-top: var(--spacing-4);
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.config-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.config-value {
  font-size: var(--text-xl);
  font-weight: 600;
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-4);
}

.agent-card {
  padding: var(--spacing-4);
}

.agent-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

.agent-card__header h3 {
  margin: 0;
  font-size: var(--text-base);
}

.agent-card__stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-3);
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat__label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.stat__value {
  font-size: var(--text-sm);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.agent-card__reasoning {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  padding: var(--spacing-2);
  background-color: var(--color-bg-tertiary);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-3);
  line-height: var(--leading-relaxed);
}

.agent-card__time {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.disruptions-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.disruption-card {
  padding: var(--spacing-5);
}

.disruption-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

.disruption-header h3 {
  margin: 0;
}

.disruption-reasoning {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-3);
  line-height: var(--leading-relaxed);
}

.disruption-actions h4 {
  font-size: var(--text-sm);
  margin-bottom: var(--spacing-2);
  color: var(--color-text-secondary);
}

.disruption-actions ul {
  list-style: disc;
  padding-left: var(--spacing-4);
  margin: 0;
}

.disruption-actions li {
  font-size: var(--text-sm);
  margin-bottom: var(--spacing-1);
  color: var(--color-text);
}

.response-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-4);
}

.response-card h3 {
  margin-bottom: var(--spacing-4);
  font-size: var(--text-base);
}

.reports-placeholder {
  text-align: center;
  padding: var(--spacing-12);
}

.success-icon {
  color: var(--color-success);
  margin-bottom: var(--spacing-4);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  text-align: center;
}

.loading-state p {
  margin-top: var(--spacing-4);
  color: var(--color-text-secondary);
}

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

.error-state__title {
  font-size: var(--text-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-2);
}

.error-state__text {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-6);
}

.step-navigation {
  display: flex;
  justify-content: space-between;
  padding-top: var(--spacing-6);
  border-top: 1px solid var(--color-border);
  margin-top: var(--spacing-6);
}

.setup-actions {
  margin-top: var(--spacing-6);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border);
}

.monitoring-actions {
  margin-bottom: var(--spacing-6);
}
</style>
