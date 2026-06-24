<template>
  <section class="page home-page">
    <div class="page-header hero">
      <div class="hero-copy">
        <span class="eyebrow">ProductShot Agent</span>
        <h1 class="page-title">上传一张商品图，生成一整套营销素材</h1>
        <p class="page-description">
          ProductShot Agent 可以帮助小商家自动生成商品场景图、社媒封面、卖点文案和发布内容。
        </p>
        <div class="hero-actions">
          <el-button class="orange-button" type="primary" size="large" @click="$router.push('/create')">
            创建项目
          </el-button>
          <el-button size="large" @click="$router.push('/history')">查看历史项目</el-button>
        </div>
      </div>
      <div class="hero-preview">
        <div class="studio-card panel">
          <div class="studio-head">
            <span class="metric-pill accent">Live Workflow</span>
            <span class="muted">7 steps</span>
          </div>
          <div class="studio-brief">
            <span>Brief</span>
            <strong>手工香薰蜡烛</strong>
            <p>礼物场景 · 生活方式 · 小红书首图</p>
          </div>
          <div class="studio-flow">
            <div v-for="item in studioFlow" :key="item" class="flow-line">
              <span></span>
              <strong>{{ item }}</strong>
            </div>
          </div>
          <div class="output-board">
            <div class="output-shot primary-shot">
              <span>Scene</span>
            </div>
            <div class="output-shot">
              <span>Copy</span>
            </div>
            <div class="output-shot">
              <span>Score</span>
            </div>
          </div>
        </div>
      </div>
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
import { ChatLineRound, MagicStick, PictureRounded } from '@element-plus/icons-vue'

const studioFlow = ['商品分析', '创意策划', 'Prompt 构建', '图片生成', '评分迭代', '文案导出']

const flow = [
  { title: '分析商品', text: '根据图片和卖点生成商品类型、人群、视觉风格和原图问题。', icon: PictureRounded },
  { title: '规划创意', text: '自动输出 3 个可选营销方向，覆盖白底、电商、种草和促销场景。', icon: MagicStick },
  { title: '评价迭代', text: '对生成图评分，给出修改建议，并支持自然语言二次调整。', icon: ChatLineRound }
]
</script>

<style scoped>
.hero {
  align-items: center;
  min-height: 520px;
  margin-bottom: 38px;
}

.hero-copy {
  max-width: 760px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 30px;
}

.hero-preview {
  width: min(440px, 100%);
}

.studio-card {
  position: relative;
  display: grid;
  gap: 18px;
  padding: 18px;
  overflow: hidden;
}

.studio-card::before {
  position: absolute;
  inset: 0;
  border-left: 5px solid var(--ps-primary);
  pointer-events: none;
  content: "";
}

.studio-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.studio-brief {
  padding: 20px;
  border: 1px solid rgba(18, 63, 50, 0.14);
  border-radius: var(--ps-radius);
  background: var(--ps-bg-ink);
  color: var(--ps-surface);
}

.studio-brief span {
  color: rgba(255, 253, 248, 0.62);
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}

.studio-brief strong {
  display: block;
  margin-top: 8px;
  font-family: Georgia, "Times New Roman", "Songti SC", serif;
  font-size: 28px;
  font-weight: 650;
}

.studio-brief p {
  margin: 10px 0 0;
  color: rgba(255, 253, 248, 0.72);
}

.studio-flow {
  display: grid;
  gap: 8px;
}

.flow-line {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  color: var(--ps-muted-strong);
  font-size: 13px;
}

.flow-line span {
  width: 24px;
  height: 2px;
  background: var(--ps-accent);
}

.output-board {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr 0.8fr;
  gap: 10px;
}

.output-shot {
  display: flex;
  min-height: 96px;
  align-items: end;
  padding: 10px;
  border: 1px solid var(--ps-border);
  border-radius: var(--ps-radius);
  background:
    linear-gradient(135deg, rgba(18, 63, 50, 0.08), rgba(229, 111, 79, 0.12)),
    var(--ps-surface-quiet);
}

.primary-shot {
  min-height: 132px;
  background:
    linear-gradient(140deg, rgba(18, 63, 50, 0.92) 0 52%, rgba(229, 111, 79, 0.92) 52% 100%),
    var(--ps-bg-ink);
}

.output-shot span {
  color: var(--ps-muted-strong);
  font-size: 13px;
  font-weight: 800;
}

.primary-shot span {
  color: var(--ps-surface);
}

.flow-icon {
  width: 28px;
  height: 28px;
  color: var(--ps-accent);
}

.agent-card h3 {
  margin: 14px 0 8px;
  font-size: 18px;
}

.agent-card p {
  margin: 0;
  color: var(--ps-muted);
  line-height: 1.7;
}

@media (max-width: 900px) {
  .hero-preview {
    width: 100%;
  }

  .hero {
    min-height: 0;
  }
}
</style>
