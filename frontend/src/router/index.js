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