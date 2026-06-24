<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="shell-primary">
        <RouterLink class="brand" to="/">
          <div class="brand-mark">PS</div>
          <div>
            <p class="brand-title">ProductShot</p>
            <p class="brand-subtitle">Agent workspace</p>
          </div>
        </RouterLink>

        <RouterLink class="new-project-link" to="/studio">
          <el-icon :size="16">
            <Plus />
          </el-icon>
          <span>新建项目</span>
        </RouterLink>
      </div>

      <section class="shell-history" aria-label="项目历史">
        <div class="shell-history-head">
          <div>
            <p class="section-kicker">History</p>
            <h2 class="section-title">项目历史</h2>
          </div>
          <button class="icon-button" type="button" aria-label="刷新项目历史" @click="loadProjects">
            <el-icon :size="16">
              <Refresh />
            </el-icon>
          </button>
        </div>
        <div v-if="projects.length" class="shell-project-list">
          <RouterLink
            v-for="project in projects"
            :key="project.id"
            class="shell-project-row"
            :class="{ active: project.id === currentProjectId }"
            :to="`/studio/${project.id}`"
          >
            <strong>{{ project.product_name }}</strong>
            <span>{{ project.target_platform }} · {{ statusLabel(project.status) }}</span>
          </RouterLink>
        </div>
        <p v-else-if="projectsLoading" class="shell-muted">正在加载项目...</p>
        <p v-else class="shell-muted">{{ projectError || '暂无历史项目' }}</p>
      </section>

      <div class="shell-footer">
        <RouterLink class="settings-button" to="/model-settings" aria-label="模型管理">
          <el-icon :size="18">
            <Setting />
          </el-icon>
        </RouterLink>
        <div class="shell-status">Mock Ready</div>
      </div>
    </aside>

    <header class="mobile-shell-bar">
      <div class="mobile-shell-top">
        <RouterLink class="brand" to="/">
          <div class="brand-mark">PS</div>
          <div>
            <p class="brand-title">ProductShot</p>
            <p class="brand-subtitle">Agent workspace</p>
          </div>
        </RouterLink>
        <button
          class="mobile-menu-button"
          type="button"
          :aria-expanded="mobileNavOpen"
          aria-label="切换导航菜单"
          @click="mobileNavOpen = !mobileNavOpen"
        >
          <el-icon :size="18">
            <Close v-if="mobileNavOpen" />
            <Menu v-else />
          </el-icon>
        </button>
      </div>
      <div v-show="mobileNavOpen" class="mobile-menu-panel">
        <RouterLink class="new-project-link" to="/studio">新建项目</RouterLink>
        <RouterLink class="nav-link" to="/model-settings">
          <el-icon :size="18">
            <Setting />
          </el-icon>
          <span>模型管理</span>
        </RouterLink>
        <section class="shell-history" aria-label="移动端项目历史">
          <div class="shell-history-head">
            <div>
              <p class="section-kicker">History</p>
              <h2 class="section-title">项目历史</h2>
            </div>
            <button class="icon-button" type="button" aria-label="刷新项目历史" @click="loadProjects">
              <el-icon :size="16">
                <Refresh />
              </el-icon>
            </button>
          </div>
          <div v-if="projects.length" class="shell-project-list">
            <RouterLink
              v-for="project in projects"
              :key="project.id"
              class="shell-project-row"
              :class="{ active: project.id === currentProjectId }"
              :to="`/studio/${project.id}`"
            >
              <strong>{{ project.product_name }}</strong>
              <span>{{ project.target_platform }} · {{ statusLabel(project.status) }}</span>
            </RouterLink>
          </div>
          <p v-else-if="projectsLoading" class="shell-muted">正在加载项目...</p>
          <p v-else class="shell-muted">{{ projectError || '暂无历史项目' }}</p>
        </section>
      </div>
    </header>

    <main class="main-shell">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Close, Menu, Plus, Refresh, Setting } from '@element-plus/icons-vue'
import { errorMessage } from '../api/client'
import { listProjects, type Project } from '../api/productshot'

const route = useRoute()
const mobileNavOpen = ref(false)
const projects = ref<Project[]>([])
const projectsLoading = ref(false)
const projectError = ref('')

const currentProjectId = computed(() => {
  const value = route.params.id
  return typeof value === 'string' ? Number(value) : 0
})

onMounted(loadProjects)

watch(
  () => route.fullPath,
  () => {
    mobileNavOpen.value = false
    loadProjects()
  }
)

async function loadProjects() {
  projectsLoading.value = true
  projectError.value = ''
  try {
    projects.value = await listProjects()
  } catch (error) {
    projectError.value = errorMessage(error)
  } finally {
    projectsLoading.value = false
  }
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    draft: '草稿',
    analyzed: '已分析',
    planned: '已出方案',
    generated: '已生成',
    reviewed: '已评分',
    copywritten: '已出文案',
    revised: '已修改',
    exported: '已导出'
  }
  return labels[status] || status
}
</script>
