<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'

const router = useRouter()
const projectStore = useProjectStore()
const expandedProject = ref(null)
const selectedProject = ref(null)
const loading = ref(false)

const projects = computed(() => projectStore.projects)

function toggleProject(projectId) {
  expandedProject.value = expandedProject.value === projectId ? null : projectId
}

function viewProject(projectId) {
  router.push(`/projects/${projectId}`)
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString(undefined, { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

function getStatusClass(status) {
  const classes = {
    active: 'success',
    idle: 'warning',
    completed: 'info',
    archived: 'secondary'
  }
  return classes[status] || 'secondary'
}

onMounted(async () => {
  loading.value = true
  try {
    await projectStore.fetchProjects()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <ProjectLayout>
    <div class="history-page">
      <div class="page-header">
        <h1>Project History</h1>
        <p class="text-secondary">View past monitoring projects and their outcomes.</p>
      </div>

      <div v-if="loading" class="loading">
        <div class="loading__spinner"></div>
      </div>

      <div v-else-if="projects.length === 0" class="empty-state">
        <svg class="empty-icon" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
        </svg>
        <h3>No projects yet</h3>
        <p>Create your first project to start monitoring supply chain disruptions.</p>
        <router-link to="/projects/new" class="btn btn--primary">New Project</router-link>
      </div>

      <div v-else class="projects-grid">
        <div 
          v-for="project in projects" 
          :key="project.id"
          :class="['project-card', { expanded: expandedProject === project.id }]"
        >
          <div class="project-card__header" @click="toggleProject(project.id)">
            <div class="project-card__title">
              <h3>{{ project.name }}</h3>
              <span :class="['status-badge', getStatusClass(project.status)]">
                {{ project.status }}
              </span>
            </div>
            <div class="project-card__meta">
              <span class="meta-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                {{ formatDate(project.created_at) }}
              </span>
              <span class="meta-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
                {{ project.config?.regions?.length || 0 }} regions
              </span>
            </div>
            <svg 
              class="expand-icon" 
              :class="{ rotated: expandedProject === project.id }"
              width="20" 
              height="20" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2"
            >
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>

          <div v-if="expandedProject === project.id" class="project-card__body">
            <div class="project-details">
              <div class="detail-section">
                <h4>Configuration</h4>
                <div class="detail-row">
                  <span class="detail-label">Regions:</span>
                  <span class="detail-value">{{ project.config?.regions?.join(', ') || 'None' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Avg Threshold:</span>
                  <span class="detail-value">
                    {{ project.config?.thresholds ? 
                      (Object.values(project.config.thresholds).reduce((a, b) => a + b, 0) / Object.keys(project.config.thresholds).length).toFixed(2) : 
                      'N/A' }}
                  </span>
                </div>
              </div>

              <div class="detail-section">
                <h4>Summary</h4>
                <div class="summary-stats">
                  <div class="stat-item">
                    <span class="stat-value">0</span>
                    <span class="stat-label">Disruptions</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">0</span>
                    <span class="stat-label">Reports</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ project.config?.regions?.length || 0 }}</span>
                    <span class="stat-label">Agents</span>
                  </div>
                </div>
              </div>

              <div class="project-actions">
                <button class="btn btn--primary" @click="viewProject(project.id)">
                  View Details
                </button>
                <button class="btn btn--secondary" @click="router.push(`/projects/${project.id}/reports`)">
                  View Reports
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.history-page {
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: var(--spacing-6);
}

.page-header h1 {
  margin-bottom: var(--spacing-1);
}

.text-secondary {
  color: var(--color-text-secondary);
}

.projects-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.project-card {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all var(--transition-fast);
}

.project-card:hover {
  border-color: var(--color-primary);
}

.project-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4);
  cursor: pointer;
}

.project-card__title {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.project-card__title h3 {
  margin: 0;
}

.status-badge {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
}

.status-badge.success {
  background-color: rgba(34, 197, 94, 0.1);
  color: var(--color-low);
}

.status-badge.warning {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--color-medium);
}

.status-badge.info {
  background-color: rgba(59, 130, 246, 0.1);
  color: var(--color-primary);
}

.status-badge.secondary {
  background-color: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

.project-card__meta {
  display: flex;
  gap: var(--spacing-4);
  margin-top: var(--spacing-1);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.expand-icon {
  transition: transform var(--transition-fast);
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

.project-card__body {
  padding: var(--spacing-4);
  border-top: 1px solid var(--color-border);
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.project-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.detail-section h4 {
  margin-bottom: var(--spacing-2);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-1) 0;
  border-bottom: 1px solid var(--color-border-light);
}

.detail-label {
  color: var(--color-text-secondary);
}

.detail-value {
  font-weight: 500;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-3);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-3);
  background-color: var(--color-bg-secondary);
  border-radius: var(--radius-md);
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 700;
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.project-actions {
  display: flex;
  gap: var(--spacing-2);
  margin-top: var(--spacing-2);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  text-align: center;
}

.empty-icon {
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-4);
}
</style>