<template>
  <div class="app-layout">
    <aside class="sidebar">
      <RouterLink class="brand" to="/">
        <div class="brand-mark">PS</div>
        <div>
          <p class="brand-title">ProductShot</p>
          <p class="brand-subtitle">Marketing Agent Studio</p>
        </div>
      </RouterLink>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.to" class="nav-link" :to="item.to">
          <el-icon :size="18">
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="shell-status">Mock Provider Ready</div>
    </aside>
    <main class="main-shell">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { EditPen, FolderOpened, HomeFilled, MagicStick, Picture, TrendCharts } from '@element-plus/icons-vue'

const navItems = [
  { label: '首页', to: '/', icon: HomeFilled },
  { label: '创建项目', to: '/create', icon: EditPen },
  { label: '工作流', to: '/workflow/1', icon: MagicStick },
  { label: '创意方案', to: '/plans/1', icon: TrendCharts },
  { label: '生成结果', to: '/results/1', icon: Picture },
  { label: '历史项目', to: '/history', icon: FolderOpened }
]
</script>
