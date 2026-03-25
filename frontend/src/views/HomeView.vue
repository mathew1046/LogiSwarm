<script setup>
import { onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'

const projectStore = useProjectStore()

onMounted(async () => {
  await projectStore.fetchProjects()
})
</script>

<template>
  <div>
    <h1>LogiSwarm</h1>
    <p>Geo-aware swarm intelligence for supply chain disruption detection</p>
    <router-link to="/projects/new" class="btn btn--primary">New Project</router-link>
    
    <h2>Recent Projects</h2>
    <div v-if="projectStore.loading" class="loading">
      <div class="loading__spinner"></div>
    </div>
    <div v-else-if="projectStore.projects.length === 0" class="empty-state">
      <p class="empty-state__title">No projects yet</p>
      <p class="empty-state__text">Create your first project to start monitoring supply chain disruptions.</p>
    </div>
    <div v-else class="grid grid--3">
      <div v-for="project in projectStore.projects" :key="project.id" class="card">
        <h3>{{ project.name }}</h3>
        <p>Status: {{ project.status }}</p>
        <router-link :to="`/projects/${project.id}`" class="btn btn--secondary btn--sm">View</router-link>
      </div>
    </div>
  </div>
</template>