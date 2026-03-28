<!--
LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
Copyright (C) 2025 LogiSwarm Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
-->

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