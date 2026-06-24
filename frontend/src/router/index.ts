import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import CreateProjectView from '../views/CreateProjectView.vue'
import WorkflowView from '../views/WorkflowView.vue'
import PlansView from '../views/PlansView.vue'
import ResultsView from '../views/ResultsView.vue'
import HistoryView from '../views/HistoryView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/create', name: 'create', component: CreateProjectView },
    { path: '/workflow/:id', name: 'workflow', component: WorkflowView, props: true },
    { path: '/plans/:id', name: 'plans', component: PlansView, props: true },
    { path: '/results/:id', name: 'results', component: ResultsView, props: true },
    { path: '/history', name: 'history', component: HistoryView }
  ]
})

export default router

