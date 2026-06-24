import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ProjectStudioView from '../views/ProjectStudioView.vue'
import ModelSettingsView from '../views/ModelSettingsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/studio', name: 'studio-create', component: ProjectStudioView },
    { path: '/studio/:id', name: 'studio', component: ProjectStudioView },
    { path: '/create', redirect: '/studio' },
    { path: '/workflow/:id', redirect: (to) => `/studio/${to.params.id}` },
    { path: '/plans/:id', redirect: (to) => `/studio/${to.params.id}` },
    { path: '/results/:id', redirect: (to) => `/studio/${to.params.id}` },
    { path: '/history', redirect: '/studio' },
    { path: '/model-settings', name: 'model-settings', component: ModelSettingsView }
  ]
})

export default router
