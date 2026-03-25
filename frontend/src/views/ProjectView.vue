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
const completedSteps = ref([])

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

function getSeverityBadgeClass(severity) {
  const s = (severity || 'low').toLowerCase()
  return `badge--${s}`
}

function formatDate(date) {
  return new Date(date).toLocaleString()
}

onMounted(async () => {
  if (route.params.id) {
    await projectStore.fetchProject(route.params.id)
    await agentStore.fetchAgents()
  }
})

function goToStep(stepId) {
  const currentIndex = steps.findIndex(s => s.id === activeStep.value)
  const targetIndex = steps.findIndex(s => s.id === stepId)
  
  if (targetIndex <= currentIndex || completedSteps.value.includes(stepId)) {
    activeStep.value = stepId
  }
}

function goToMap() {
  if (currentProject.value) {
    router.push(`/projects/${currentProject.value.id}/map`)
  }
}

function goToReports() {
  if (currentProject.value) {
    router.push(`/projects/${currentProject.value.id}/reports`)
  }
}
</script>

<template>
  <ProjectLayout>
    <div class="project-view">
      <header class="project-header">
        <div class="project-header__title">
          <h1>{{ currentProject?.name || 'Project Dashboard' }}</h1>
          <span class="badge badge--low">{{ currentProject?.status || 'idle' }}</span>
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

      <StepWorkflow 
        :steps="steps" 
        :active-step="activeStep" 
        :completed-steps="completedSteps"
      >
        <div class="step-panel">
          <!-- Setup Step -->
          <div v-if="activeStep === 'setup'" class="step-section">
            <h2>Setup</h2>
            <p class="text-secondary">Configure your monitoring regions and thresholds.</p>
            
            <div class="setup-summary card">
              <h3>Configuration</h3>
              <div class="config-grid">
                <div class="config-item">
                  <span class="config-label">Monitored Regions</span>
                  <span class="config-value">{{ currentProject?.config?.regions?.length || 0 }} regions</span>
                </div>
                <div class="config-item">
                  <span class="config-label">Average Threshold</span>
                  <span class="config-value">
                    {{ currentProject?.config?.thresholds ? 
                      (Object.values(currentProject.config.thresholds).reduce((a, b) => a + b, 0) / Object.keys(currentProject.config.thresholds).length).toFixed(2) : 
                      '0.75' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Monitoring Step -->
          <div v-else-if="activeStep === 'monitoring'" class="step-section">
            <h2>Agent Monitoring</h2>
            <p class="text-secondary">Live status of all geo-agents monitoring your supply chain.</p>
            
            <div v-if="agentStore.loading" class="loading">
              <div class="loading__spinner"></div>
            </div>
            
            <div v-else class="agents-grid">
              <div v-for="agent in agents" :key="agent.region_id" class="agent-card card">
                <div class="agent-card__header">
                  <h3>{{ agent.region_name }}</h3>
                  <span :class="['badge', getSeverityBadgeClass(agent.last_assessment?.severity)]">
                    {{ agent.last_assessment?.severity || 'LOW' }}
                  </span>
                </div>
                <div class="agent-card__stats">
                  <div class="stat">
                    <span class="stat__label">Confidence</span>
                    <span class="stat__value">
                      {{ ((agent.last_assessment?.confidence || 0) * 100).toFixed(1) }}%
                    </span>
                  </div>
                  <div class="stat">
                    <span class="stat__label">Status</span>
                    <span class="stat__value">{{ agent.running ? 'Running' : 'Stopped' }}</span>
                  </div>
                </div>
                <div class="agent-card__reasoning" v-if="agent.last_assessment?.reasoning">
                  <p>{{ agent.last_assessment.reasoning }}</p>
                </div>
                <div class="agent-card__time">
                  Last cycle: {{ agent.last_cycle_at ? formatDate(agent.last_cycle_at) : 'Never' }}
                </div>
              </div>
            </div>
          </div>

          <!-- Disruption Step -->
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
              <div v-for="agent in highRiskAgents" :key="agent.region_id" class="disruption-card card">
                <div class="disruption-header">
                  <h3>{{ agent.region_name }}</h3>
                  <span :class="['badge', getSeverityBadgeClass(agent.last_assessment?.severity)]">
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

          <!-- Response Step -->
          <div v-else-if="activeStep === 'response'" class="step-section">
            <h2>Response Actions</h2>
            <p class="text-secondary">Recommended and automated responses to detected disruptions.</p>
            
            <div class="response-grid">
              <div class="response-card card">
                <h3>Pending Actions</h3>
                <div class="empty-state">
                  <p class="text-secondary">No pending actions at this time.</p>
                </div>
              </div>
              <div class="response-card card">
                <h3>Completed Actions</h3>
                <div class="empty-state">
                  <p class="text-secondary">No completed actions yet.</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Report Step -->
          <div v-else-if="activeStep === 'report'" class="step-section">
            <h2>Reports</h2>
            <p class="text-secondary">Post-disruption analysis reports and insights.</p>
            
            <div class="reports-placeholder card">
              <button class="btn btn--primary" @click="goToReports">
                View All Reports
              </button>
            </div>
          </div>
        </div>
      </StepWorkflow>
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
}

.project-header__actions {
  display: flex;
  gap: var(--spacing-2);
}

.step-section {
  padding: var(--spacing-6);
}

.step-section h2 {
  margin-bottom: var(--spacing-2);
}

.text-secondary {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-6);
}

.setup-summary {
  background-color: var(--color-surface);
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
  background-color: var(--color-surface);
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
}

.agent-card__reasoning {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  padding: var(--spacing-2);
  background-color: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-3);
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
  border-left: 4px solid var(--color-high);
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
}

.disruption-actions h4 {
  font-size: var(--text-sm);
  margin-bottom: var(--spacing-2);
}

.disruption-actions ul {
  list-style: disc;
  padding-left: var(--spacing-4);
  margin: 0;
}

.disruption-actions li {
  font-size: var(--text-sm);
  margin-bottom: var(--spacing-1);
}

.response-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-4);
}

.response-card h3 {
  margin-bottom: var(--spacing-4);
}

.reports-placeholder {
  text-align: center;
  padding: var(--spacing-12);
}

.success-icon {
  color: var(--color-success);
  margin-bottom: var(--spacing-4);
}
</style>