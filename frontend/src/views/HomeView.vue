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
    description: 'Region-specific AI agents monitor live feeds and detect disruptions before they cascade.',
    color: 'primary'
  },
  {
    icon: 'feeds',
    title: 'Live Feeds',
    description: 'Real-time data from AIS tracking, weather APIs, port sensors, and geopolitical news.',
    color: 'info'
  },
  {
    icon: 'cascade',
    title: 'Cascade Model',
    description: 'Weighted propagation model predicts how disruptions spread across global trade lanes.',
    color: 'warning'
  },
  {
    icon: 'reroute',
    title: 'Auto-Reroute',
    description: 'Automatic carrier rebooking and TMS integration when risk thresholds are exceeded.',
    color: 'success'
  },
  {
    icon: 'reports',
    title: 'Analysis Reports',
    description: 'Post-disruption analysis with timeline, cascade impact, and lessons learned.',
    color: 'secondary'
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

const iconPaths = {
  agents: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
  feeds: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
  cascade: 'M13 10V3L4 14h7v7l9-11h-7z',
  reroute: 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7',
  reports: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
}
</script>

<template>
  <div class="home-page">
    <section class="hero">
      <div class="hero-bg"></div>
      <div class="hero-grid"></div>
      <div class="hero-radial"></div>

      <div class="hero-content fade-in">
        <div class="hero-badge">
          <span class="status-dot status-dot--active"></span>
          <span>v0.2.0 — Now Monitoring 8 Regions</span>
        </div>

        <h1 class="hero-title">
          <span class="hero-title__text">LogiSwarm</span>
          <span class="hero-title__glow"></span>
        </h1>

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

      <div class="hero-visual">
        <div class="radar-sweep"></div>
        <div class="radar-ring radar-ring--1"></div>
        <div class="radar-ring radar-ring--2"></div>
        <div class="radar-ring radar-ring--3"></div>
        <div class="radar-dots">
          <div class="radar-dot radar-dot--1"></div>
          <div class="radar-dot radar-dot--2"></div>
          <div class="radar-dot radar-dot--3"></div>
          <div class="radar-dot radar-dot--4"></div>
          <div class="radar-dot radar-dot--5"></div>
        </div>
      </div>
    </section>

    <section class="features">
      <h2 class="section-title">Core Capabilities</h2>
      <div class="features-grid">
        <div
          v-for="feature in features"
          :key="feature.icon"
          class="feature-card card card--glass card-lift"
          :style="{ '--accent-color': `var(--color-${feature.color})` }"
        >
          <div class="feature-icon" :style="{ backgroundColor: `var(--color-${feature.color}-bg)`, color: `var(--color-${feature.color})` }">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path :d="iconPaths[feature.icon]" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-description">{{ feature.description }}</p>
          <div class="feature-accent"></div>
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
        <svg class="empty-state__icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <p class="empty-state__title">No projects yet</p>
        <p class="empty-state__text">Create your first project to start monitoring supply chain disruptions.</p>
        <button class="btn btn--primary" @click="createNewProject">Create Project</button>
      </div>

      <div v-else class="projects-list">
        <div
          v-for="project in recentProjects"
          :key="project.id"
          class="project-item card card-lift"
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
  position: relative;
  padding: var(--spacing-16) var(--spacing-6);
  min-height: 540px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, var(--color-bg) 0%, var(--color-bg-secondary) 50%, var(--color-bg-tertiary) 100%);
  z-index: 0;
}

.hero-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(var(--color-border) 1px, transparent 1px),
    linear-gradient(90deg, var(--color-border) 1px, transparent 1px);
  background-size: 60px 60px;
  opacity: 0.15;
  z-index: 1;
}

.hero-radial {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 800px;
  height: 800px;
  background: radial-gradient(circle, var(--color-primary-glow) 0%, transparent 70%);
  opacity: 0.15;
  z-index: 2;
}

.hero-content {
  position: relative;
  z-index: 10;
  max-width: 700px;
  text-align: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-6);
}

.hero-title {
  position: relative;
  font-size: var(--text-4xl);
  font-weight: 700;
  letter-spacing: -0.03em;
  margin-bottom: var(--spacing-4);
}

.hero-title__text {
  position: relative;
  z-index: 1;
  color: var(--color-text);
}

.hero-title__glow {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  height: 40px;
  background: var(--color-primary);
  filter: blur(40px);
  opacity: 0.4;
  z-index: 0;
}

.hero-subtitle {
  font-size: var(--text-xl);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-4);
  font-weight: 500;
}

.hero-description {
  font-size: var(--text-base);
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-8);
  line-height: var(--leading-relaxed);
  max-width: 540px;
  margin-left: auto;
  margin-right: auto;
}

.hero-actions {
  display: flex;
  gap: var(--spacing-4);
  justify-content: center;
  flex-wrap: wrap;
}

.hero-visual {
  position: absolute;
  right: 10%;
  top: 50%;
  transform: translateY(-50%);
  width: 300px;
  height: 300px;
  z-index: 5;
  display: none;
}

@media (min-width: 1200px) {
  .hero-visual {
    display: block;
  }
}

.radar-sweep {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 200px;
  height: 200px;
  transform: translate(-50%, -50%);
  background: conic-gradient(from 0deg, transparent 0deg, var(--color-primary) 30deg, transparent 60deg);
  border-radius: 50%;
  animation: radarSweep 4s linear infinite;
  opacity: 0.3;
}

@keyframes radarSweep {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to { transform: translate(-50%, -50%) rotate(360deg); }
}

.radar-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border: 1px solid var(--color-primary);
  border-radius: 50%;
  opacity: 0.2;
}

.radar-ring--1 { width: 80px; height: 80px; }
.radar-ring--2 { width: 140px; height: 140px; }
.radar-ring--3 { width: 200px; height: 200px; }

.radar-dots {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.radar-dot {
  position: absolute;
  width: 6px;
  height: 6px;
  background: var(--color-primary);
  border-radius: 50%;
  animation: radarPulse 3s ease-in-out infinite;
}

.radar-dot--1 { top: -70px; left: 0; animation-delay: 0s; }
.radar-dot--2 { top: -40px; left: 50px; animation-delay: 0.5s; }
.radar-dot--3 { top: 0; left: 80px; animation-delay: 1s; }
.radar-dot--4 { top: 50px; left: 30px; animation-delay: 1.5s; }
.radar-dot--5 { top: 70px; left: -20px; animation-delay: 2s; }

@keyframes radarPulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.5); }
}

.section-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-6);
}

.features {
  padding: var(--spacing-12) var(--spacing-6);
  background: var(--color-bg-secondary);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--spacing-5);
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  position: relative;
  text-align: left;
  padding: var(--spacing-6);
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--accent-color);
  opacity: 0.6;
}

.feature-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
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

.feature-accent {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 80px;
  height: 80px;
  background: radial-gradient(circle at bottom right, var(--accent-color), transparent 70%);
  opacity: 0.05;
}

.recent-projects {
  padding: var(--spacing-12) var(--spacing-6);
  max-width: 900px;
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
  transition: transform var(--transition-fast), color var(--transition-fast);
}

.project-item:hover .project-item__arrow {
  transform: translateX(4px);
  color: var(--color-primary);
}
</style>
