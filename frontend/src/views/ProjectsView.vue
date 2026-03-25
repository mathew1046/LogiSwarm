<script setup>
import { onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'

const projectStore = useProjectStore()

onMounted(async () => {
  await projectStore.fetchProjects()
})
</script>

<template>
  <ProjectLayout>
    <div>
      <h1>Projects</h1>
      <router-link to="/projects/new" class="btn btn--primary">New Project</router-link>
      
      <div v-if="projectStore.loading" class="loading">
        <div class="loading__spinner"></div>
      </div>
      <div v-else-if="projectStore.projects.length === 0" class="empty-state">
        <p class="empty-state__title">No projects</p>
        <p class="empty-state__text">Create a project to start monitoring.</p>
      </div>
      <div v-else class="grid grid--2">
        <div v-for="project in projectStore.projects" :key="project.id" class="card">
          <h3>{{ project.name }}</h3>
          <p>Status: {{ project.status }}</p>
          <p>Created: {{ new Date(project.created_at).toLocaleDateString() }}</p>
          <router-link :to="`/projects/${project.id}`" class="btn btn--secondary btn--sm">View</router-link>
        </div>
      </div>
    </div>
  </ProjectLayout>
</template>