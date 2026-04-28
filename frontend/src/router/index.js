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

import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: 'LogiSwarm - Supply Chain Intelligence' }
  },
  {
    path: '/projects',
    name: 'projects',
    component: () => import('../views/ProjectsView.vue'),
    meta: { title: 'Projects' }
  },
  {
    path: '/projects/new',
    name: 'project-new',
    component: () => import('../views/ProjectCreateView.vue'),
    meta: { title: 'New Project' }
  },
  {
    path: '/projects/:id',
    name: 'project',
    component: () => import('../views/ProjectView.vue'),
    meta: { title: 'Project Dashboard' }
  },
  {
    path: '/projects/:id/map',
    name: 'project-map',
    component: () => import('../views/ProjectMapView.vue'),
    meta: { title: 'Risk Map' }
  },
  {
    path: '/projects/:id/reports',
    name: 'project-reports',
    component: () => import('../views/ProjectReportsView.vue'),
    meta: { title: 'Reports' }
  },
  {
    path: '/projects/:id/interact',
    name: 'project-interact',
    component: () => import('../views/ProjectInteractView.vue'),
    meta: { title: 'Interact' }
  },
  {
    path: '/history',
    name: 'history',
    component: () => import('../views/HistoryView.vue'),
    meta: { title: 'History' }
  },
  {
    path: '/simulation',
    name: 'simulation',
    component: () => import('../views/SimulationView.vue'),
    meta: { title: 'Simulation' }
  },
  {
    path: '/agents',
    name: 'agents',
    component: () => import('../views/AgentMapView.vue'),
    meta: { title: 'Agent Map' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFoundView.vue'),
    meta: { title: 'Not Found' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to, _from, next) => {
  document.title = to.meta.title || 'LogiSwarm'
  next()
})

export default router