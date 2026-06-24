<template>
  <section class="page">
    <div class="page-header">
      <div>
        <span class="eyebrow">Project Archive</span>
        <h1 class="page-title">历史项目</h1>
        <p class="page-description">查看本地 SQLite 中保存的商品营销项目，继续编辑或查看生成结果。</p>
      </div>
      <el-button class="orange-button" type="primary" @click="$router.push('/studio')">创建项目</el-button>
    </div>

    <div class="panel panel-pad">
      <div class="history-head">
        <div>
          <p class="section-kicker">Saved briefs</p>
          <h2 class="section-title">本地项目记录</h2>
        </div>
        <span class="metric-pill">{{ projects.length }} 个项目</span>
      </div>
      <el-table v-loading="loading" :data="projects" style="width: 100%">
        <el-table-column prop="product_name" label="商品名称" min-width="180" />
        <el-table-column prop="target_platform" label="目标平台" width="120" />
        <el-table-column prop="status" label="状态" width="130">
          <template #default="{ row }">
            <el-tag>{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="180">
          <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="$router.push(`/studio/${row.id}`)">继续编辑</el-button>
            <el-button text type="primary" @click="$router.push(`/studio/${row.id}`)">查看结果</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listProjects, Project } from '../api/productshot'
import { errorMessage } from '../api/client'

const projects = ref<Project[]>([])
const loading = ref(false)

onMounted(load)

async function load() {
  loading.value = true
  try {
    projects.value = await listProjects()
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    loading.value = false
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
.history-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.history-head .section-title {
  margin-bottom: 0;
}

@media (max-width: 700px) {
  .history-head {
    flex-direction: column;
  }
}
</style>
