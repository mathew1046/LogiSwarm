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
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'

const router = useRouter()
const projectStore = useProjectStore()

const recentProjects = computed(() => projectStore.projects.slice(0, 5))

const features = [
  {
    icon: 'agents',
    title: 'Geo Agents',
    description: 'Region-specific AI agents monitor live feeds and detect disruptions before they cascade.'
  },
  {
    icon: 'feeds',
    title: 'Live Feeds',
    description: 'Real-time data from AIS tracking, weather APIs, port sensors, and geopolitical news.'
  },
  {
    icon: 'cascade',
    title: 'Cascade Model',
    description: 'Weighted propagation model predicts how disruptions spread across global trade lanes.'
  },
  {
    icon: 'reroute',
    title: 'Auto-Reroute',
    description: 'Automatic carrier rebooking and TMS integration when risk thresholds are exceeded.'
  },
  {
    icon: 'reports',
    title: 'Analysis Reports',
    description: 'Post-disruption analysis with timeline, cascade impact, and lessons learned.'
  }
]

onMounted(async () => {
  await projectStore.fetchProjects()
})

function createNewProject() {
  router.push('/projects/new')
}

function goToProject(projectId) {
  router.push(`/projects/${projectId}`)
}
</script>

<template>
  <div class="home-page">
    <section class="hero">
      <div class="hero-content">
        <span class="version-badge">v0.1.0</span>
        <h1 class="hero-title">LogiSwarm</h1>
        <p class="hero-subtitle">Geo-aware swarm intelligence for supply chain disruption detection</p>
        <p class="hero-description">
          Monitor global shipping routes in real-time. Detect disruptions before they cascade.
          Get automated reroute recommendations powered by AI agents.
        </p>
        <div class="hero-actions">
          <button class="btn btn--primary btn--lg" @click="createNewProject">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 4v16m8-8H4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            New Project
          </button>
          <router-link to="/projects" class="btn btn--secondary btn--lg">
            View Projects
          </router-link>
        </div>
      </div>
    </section>

    <section class="features">
      <h2 class="section-title">Core Capabilities</h2>
      <div class="features-grid">
        <div v-for="feature in features" :key="feature.icon" class="feature-card card">
          <div class="feature-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
            </svg>
          </div>
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-description">{{ feature.description }}</p>
        </div>
      </div>
    </section>

    <section class="recent-projects">
      <div class="section-header">
        <h2 class="section-title">Recent Projects</h2>
        <router-link to="/projects" class="btn btn--secondary btn--sm">View All</router-link>
      </div>
      
      <div v-if="projectStore.loading" class="loading">
        <div class="loading__spinner"></div>
      </div>
      
      <div v-else-if="recentProjects.length === 0" class="empty-state">
        <p class="empty-state__title">No projects yet</p>
        <p class="empty-state__text">Create your first project to start monitoring supply chain disruptions.</p>
        <button class="btn btn--primary" @click="createNewProject">Create Project</button>
      </div>
      
      <div v-else class="projects-list">
        <div 
          v-for="project in recentProjects" 
          :key="project.id" 
          class="project-item card"
          @click="goToProject(project.id)"
        >
          <div class="project-item__content">
            <h3 class="project-item__name">{{ project.name }}</h3>
            <div class="project-item__meta">
              <span :class="['badge', `badge--${project.status === 'active' ? 'low' : 'medium'}`]">
                {{ project.status }}
              </span>
              <span class="project-item__date">
                Created {{ new Date(project.created_at).toLocaleDateString() }}
              </span>
            </div>
          </div>
          <svg class="project-item__arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 18l6-6-6-6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
}

.hero {
  padding: var(--spacing-12) var(--spacing-6);
  text-align: center;
  background: linear-gradient(135deg, var(--color-bg) 0%, var(--color-bg-secondary) 100%);
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero-title {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: var(--spacing-3);
}

.hero-subtitle {
  font-size: var(--text-lg);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-4);
}

.hero-description {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-6);
  line-height: var(--leading-relaxed);
}

.hero-actions {
  display: flex;
  gap: var(--spacing-4);
  justify-content: center;
  flex-wrap: wrap;
}

.section-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-6);
}

.features {
  padding: var(--spacing-10) var(--spacing-6);
  background-color: var(--color-bg-secondary);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-5);
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  text-align: center;
  padding: var(--spacing-6);
}

.feature-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-full);
  background-color: var(--color-primary);
  color: var(--color-text-inverse);
  margin-bottom: var(--spacing-4);
}

.feature-title {
  font-size: var(--text-lg);
  font-weight: 600;
  margin-bottom: var(--spacing-2);
}

.feature-description {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
}

.recent-projects {
  padding: var(--spacing-10) var(--spacing-6);
  max-width: 800px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-6);
}

.projects-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.project-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.project-item:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}

.project-item__content {
  flex: 1;
}

.project-item__name {
  font-size: var(--text-lg);
  font-weight: 600;
  margin-bottom: var(--spacing-2);
}

.project-item__meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.project-item__date {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
}

.project-item__arrow {
  color: var(--color-text-tertiary);
  transition: transform var(--transition-fast);
}

.project-item:hover .project-item__arrow {
  transform: translateX(4px);
  color: var(--color-primary);
}
</style>