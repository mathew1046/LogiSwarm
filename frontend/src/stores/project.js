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

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useProjectStore = defineStore('project', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const projectCount = computed(() => projects.value.length)

  async function fetchProjects() {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/projects')
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      projects.value = data.data || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(id) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/projects/${id}`)
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      currentProject.value = data.data
      return data.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function createProject(projectData) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(projectData)
      })
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      projects.value.push(data.data)
      return data.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  function setCurrentProject(project) {
    currentProject.value = project
  }

  function clearCurrentProject() {
    currentProject.value = null
  }

  return {
    projects,
    currentProject,
    loading,
    error,
    projectCount,
    fetchProjects,
    fetchProject,
    createProject,
    setCurrentProject,
    clearCurrentProject
  }
})