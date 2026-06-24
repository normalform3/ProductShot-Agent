<template>
  <section class="page">
    <div class="page-header">
      <div>
        <span class="eyebrow">Asset Package</span>
        <h1 class="page-title">生成结果</h1>
        <p class="page-description">完整查看“原图 -> 生成图 -> 评分 -> 文案 -> 修改 -> 导出”的营销素材链路。</p>
      </div>
      <div class="result-actions">
        <el-button :href="markdownExportUrl(id)" tag="a" target="_blank">导出 Markdown</el-button>
        <el-button :href="jsonExportUrl(id)" tag="a" target="_blank">导出 JSON</el-button>
      </div>
    </div>

    <div v-if="store.loading" class="panel panel-pad">
      <el-skeleton :rows="8" animated />
    </div>

    <template v-else-if="store.current">
      <div class="grid-2">
        <div class="panel panel-pad">
          <p class="section-kicker">Source</p>
          <h2 class="section-title">原始商品图</h2>
          <div class="image-frame original-frame">
            <img v-if="primaryAsset" :src="assetUrl(primaryAsset.file_url)" alt="原始商品图" />
            <div v-else class="empty-box">暂无原图</div>
          </div>
        </div>

        <div class="panel panel-pad">
          <p class="section-kicker">Copy bundle</p>
          <h2 class="section-title">配套文案</h2>
          <template v-if="store.current.latest_copywriting">
            <h3>{{ store.current.latest_copywriting.copywriting.title }}</h3>
            <el-tabs>
              <el-tab-pane label="小红书">
                <strong>{{ store.current.latest_copywriting.copywriting.xiaohongshu_title }}</strong>
                <p>{{ store.current.latest_copywriting.copywriting.xiaohongshu_text }}</p>
              </el-tab-pane>
              <el-tab-pane label="朋友圈">
                <p>{{ store.current.latest_copywriting.copywriting.moments_text }}</p>
              </el-tab-pane>
              <el-tab-pane label="淘宝">
                <p>{{ store.current.latest_copywriting.copywriting.taobao_text }}</p>
              </el-tab-pane>
            </el-tabs>
            <el-tag v-for="tag in store.current.latest_copywriting.copywriting.tags" :key="tag">{{ tag }}</el-tag>
          </template>
          <el-empty v-else description="选择方案生成图片后会自动生成文案" />
        </div>
      </div>

      <div class="panel panel-pad result-section">
        <div class="section-head">
          <div>
            <p class="section-kicker">Generated images</p>
            <h2 class="section-title">生成图片与评分</h2>
          </div>
          <el-button @click="$router.push(`/plans/${id}`)">重新选择方案</el-button>
        </div>
        <div v-if="store.current.generated_images.length" class="image-grid">
          <article v-for="image in store.current.generated_images" :key="image.id" class="generated-card">
            <div class="image-frame generated-frame">
              <img :src="assetUrl(image.image_url)" alt="生成图片" />
            </div>
            <div class="score-row">
              <strong>{{ image.score ? `${image.score} 分` : '待评分' }}</strong>
              <el-button text type="primary" @click="review(image)">重新评分</el-button>
            </div>
          </article>
        </div>
        <el-empty v-else description="暂无生成图片，请先选择创意方案" />
      </div>

      <div class="panel panel-pad result-section">
        <p class="section-kicker">Revision</p>
        <h2 class="section-title">自然语言修改</h2>
        <div class="revision-box">
          <el-input
            v-model="instruction"
            type="textarea"
            :rows="3"
            placeholder="例如：背景更高级一点，商品再大一些，更适合小红书封面"
          />
          <el-button class="orange-button" type="primary" :loading="revising" @click="revise">生成修改计划</el-button>
        </div>
        <div v-if="revision" class="revision-result">
          <span class="metric-pill">{{ revision.target }}</span>
          <h3>新的 Prompt</h3>
          <p>{{ revision.new_prompt.positive_prompt }}</p>
          <h3>修改计划</h3>
          <ul>
            <li v-for="item in revision.modification_plan" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { assetUrl, errorMessage } from '../api/client'
import { GeneratedImage, jsonExportUrl, markdownExportUrl, reviseProject, RevisionResponse } from '../api/productshot'
import { useProjectStore } from '../stores/project'

const props = defineProps<{ id: string }>()
const id = Number(props.id)
const store = useProjectStore()
const instruction = ref('')
const revising = ref(false)
const revision = ref<RevisionResponse | null>(null)

const primaryAsset = computed(() => store.current?.assets.find((asset) => asset.is_primary) || store.current?.assets[0])

onMounted(() => store.load(id))

async function review(image: GeneratedImage) {
  try {
    await store.review(id, image)
    ElMessage.success('评分已更新')
  } catch (error) {
    ElMessage.error(errorMessage(error))
  }
}

async function revise() {
  if (!instruction.value.trim()) {
    ElMessage.warning('请输入修改要求')
    return
  }
  revising.value = true
  try {
    revision.value = await reviseProject(id, instruction.value, store.current?.generated_images[0]?.id)
    ElMessage.success('修改计划已生成')
    await store.load(id)
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    revising.value = false
  }
}
</script>

<style scoped>
.result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.original-frame {
  height: 440px;
}

.empty-box {
  display: grid;
  height: 100%;
  place-items: center;
  color: var(--ps-muted);
}

h3 {
  margin: 0 0 12px;
  color: var(--ps-heading);
  font-size: 22px;
}

.el-tab-pane p,
.revision-result p,
li {
  color: var(--ps-muted);
  line-height: 1.8;
}

.el-tag {
  margin: 8px 8px 0 0;
}

.result-section {
  margin-top: 18px;
}

.section-head,
.score-row,
.revision-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.section-head .section-title {
  margin-bottom: 0;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.generated-card {
  border: 1px solid var(--ps-border);
  border-radius: var(--ps-radius);
  padding: 10px;
  background: var(--ps-surface-quiet);
}

.generated-frame {
  aspect-ratio: 1 / 1;
}

.score-row {
  min-height: 42px;
}

.score-row strong {
  color: var(--ps-primary);
}

.revision-result {
  margin-top: 18px;
  padding: 16px;
  border: 1px solid rgba(18, 63, 50, 0.12);
  border-radius: var(--ps-radius);
  background: var(--ps-surface-soft);
}

@media (max-width: 900px) {
  .image-grid {
    grid-template-columns: 1fr 1fr;
  }

  .section-head,
  .revision-box {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
