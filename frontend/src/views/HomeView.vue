<template>
  <section class="page home-page">
    <div class="home-console">
      <section class="home-start panel panel-pad">
        <span class="eyebrow">ProductShot Agent</span>
        <h1 class="page-title">商品素材生产工作台</h1>
        <p class="page-description">
          从一张商品原图出发，把分析、创意方案、图片生成、评分、文案和导出放在同一个连续工作区里。
        </p>
        <div class="home-actions">
          <el-button class="orange-button" type="primary" size="large" @click="$router.push('/studio')">
            新建项目
          </el-button>
          <el-button size="large" :disabled="!recentProjects.length" @click="openLatestProject">
            打开最近项目
          </el-button>
        </div>
      </section>

      <aside class="home-side panel panel-pad">
        <div class="section-head">
          <div>
            <p class="section-kicker">Recent work</p>
            <h2 class="section-title">最近项目</h2>
          </div>
          <el-button text type="primary" :loading="loading" @click="loadRecentProjects">刷新</el-button>
        </div>

        <el-alert v-if="error" class="home-alert" type="error" :title="error" :closable="false" />
        <div v-if="recentProjects.length" class="recent-list">
          <button
            v-for="project in recentProjects"
            :key="project.id"
            class="recent-row"
            type="button"
            @click="$router.push(`/studio/${project.id}`)"
          >
            <strong>{{ project.product_name }}</strong>
            <span>{{ project.target_platform }} · {{ statusLabel(project.status) }}</span>
          </button>
        </div>
        <el-empty v-else-if="!loading" description="暂无项目，先创建一个商品素材任务" />
        <el-skeleton v-else :rows="4" animated />
      </aside>
    </div>

    <div class="grid-3 flow-grid">
      <article class="agent-card" v-for="item in flow" :key="item.title">
        <component :is="item.icon" class="flow-icon" />
        <h3>{{ item.title }}</h3>
        <p>{{ item.text }}</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ChatLineRound, MagicStick, PictureRounded } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { errorMessage } from '../api/client'
import { listProjects, type Project } from '../api/productshot'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const projects = ref<Project[]>([])

const recentProjects = computed(() => projects.value.slice(0, 5))

const flow = [
  { title: '分析商品', text: '读取商品信息和原图，沉淀人群、卖点、视觉风格和图片问题。', icon: PictureRounded },
  { title: '规划创意', text: '生成多个营销方向，帮助你在生成前先比较场景、卖点和文案路线。', icon: MagicStick },
  { title: '评价迭代', text: '把生成图、评分、文案和自然语言修改集中在同一个项目上下文。', icon: ChatLineRound }
]

onMounted(loadRecentProjects)

async function loadRecentProjects() {
  loading.value = true
  error.value = ''
  try {
    projects.value = await listProjects()
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    loading.value = false
  }
}

function openLatestProject() {
  const first = recentProjects.value[0]
  if (first) {
    router.push(`/studio/${first.id}`)
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

<style scoped>
.home-console {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
  gap: 16px;
  align-items: stretch;
}

.home-start {
  display: grid;
  min-height: 430px;
  align-content: center;
  padding: 34px;
  background:
    linear-gradient(145deg, rgba(36, 88, 70, 0.08), transparent 42%),
    rgba(251, 250, 246, 0.9);
}

.home-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
}

.home-side {
  display: grid;
  align-content: start;
  gap: 14px;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.section-head .section-title {
  margin-bottom: 0;
}

.home-alert {
  margin-bottom: 2px;
}

.recent-list {
  display: grid;
  gap: 8px;
}

.recent-row {
  display: grid;
  gap: 6px;
  width: 100%;
  padding: 12px;
  border: 1px solid var(--ps-border);
  border-radius: var(--ps-radius);
  color: inherit;
  background: var(--ps-surface-quiet);
  text-align: left;
  cursor: pointer;
}

.recent-row:hover {
  border-color: rgba(36, 88, 70, 0.28);
  background: var(--ps-primary-soft);
}

.recent-row strong {
  min-width: 0;
  overflow: hidden;
  color: var(--ps-heading);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-row span {
  color: var(--ps-muted);
  font-size: 12px;
}

.flow-grid {
  margin-top: 16px;
}

.flow-icon {
  width: 26px;
  height: 26px;
  color: var(--ps-accent);
}

.agent-card h3 {
  margin: 12px 0 8px;
  font-size: 17px;
}

.agent-card p {
  margin: 0;
  color: var(--ps-muted);
  line-height: 1.65;
}

@media (max-width: 980px) {
  .home-console {
    grid-template-columns: 1fr;
  }

  .home-start {
    min-height: 0;
    padding: 24px;
  }
}
</style>
