<template>
  <section class="page studio-page">
    <div class="page-header studio-header">
      <div>
        <span class="eyebrow">Project Studio</span>
        <h1 class="page-title">{{ pageTitle }}</h1>
        <p class="page-description">
          {{ pageDescription }}
        </p>
      </div>
      <div v-if="hasProject" class="studio-actions">
        <el-button :href="markdownExportUrl(projectId)" tag="a" target="_blank">导出 Markdown</el-button>
        <el-button :href="jsonExportUrl(projectId)" tag="a" target="_blank">导出 JSON</el-button>
      </div>
    </div>

    <div class="studio-shell">
      <div class="studio-workspace">
        <WorkflowStepper :steps="store.steps" />

        <div class="studio-grid">
          <main class="studio-main">
        <section class="panel panel-pad studio-section">
          <div class="section-head">
            <div>
              <p class="section-kicker">Brief</p>
              <h2 class="section-title">商品信息与原图</h2>
            </div>
            <el-tag v-if="store.current">{{ statusLabel(store.current.status) }}</el-tag>
          </div>

          <template v-if="!hasProject">
            <el-form class="brief-form" label-position="top" :model="form" @submit.prevent>
              <div class="form-grid">
                <el-form-item label="商品名称">
                  <el-input v-model="form.product_name" placeholder="例如：手工香薰蜡烛" />
                </el-form-item>
                <el-form-item label="商品类别">
                  <el-input v-model="form.product_category" placeholder="例如：家居香氛" />
                </el-form-item>
              </div>
              <el-form-item label="核心卖点">
                <el-input
                  v-model="form.core_selling_points"
                  type="textarea"
                  :rows="4"
                  placeholder="手工制作、香味舒缓、适合作为礼物"
                />
              </el-form-item>
              <div class="form-grid">
                <el-form-item label="目标平台">
                  <el-select v-model="form.target_platform">
                    <el-option label="小红书" value="小红书" />
                    <el-option label="朋友圈" value="朋友圈" />
                    <el-option label="淘宝" value="淘宝" />
                    <el-option label="抖音" value="抖音" />
                  </el-select>
                </el-form-item>
                <el-form-item label="风格偏好">
                  <el-select v-model="form.preferred_style">
                    <el-option label="小红书生活方式风" value="小红书生活方式风" />
                    <el-option label="高级极简白底风" value="高级极简白底风" />
                    <el-option label="节日礼物促销风" value="节日礼物促销风" />
                  </el-select>
                </el-form-item>
              </div>
              <el-form-item label="目标人群">
                <el-input v-model="form.target_audience" placeholder="例如：年轻女性、租房独居人群、礼物购买者" />
              </el-form-item>
              <el-form-item label="商品图片">
                <el-upload
                  drag
                  :auto-upload="false"
                  :show-file-list="false"
                  accept=".jpg,.jpeg,.png,.webp"
                  :on-change="handleFile"
                >
                  <div class="upload-copy">点击或拖拽上传商品图</div>
                  <div class="upload-subcopy">上传后会作为后续分析、生成和文案的统一素材源。</div>
                  <template #tip>
                    <div class="el-upload__tip">支持 JPG、PNG、WebP。创建后会保存到本地 uploads。</div>
                  </template>
                </el-upload>
              </el-form-item>
              <el-button class="orange-button" type="primary" size="large" :loading="creating" @click="createStudioProject">
                创建项目并进入生产线
              </el-button>
            </el-form>
          </template>

          <template v-else-if="store.current">
            <div class="brief-summary">
              <div>
                <dt>商品名称</dt>
                <dd>{{ store.current.product_name }}</dd>
              </div>
              <div>
                <dt>目标平台</dt>
                <dd>{{ store.current.target_platform }}</dd>
              </div>
              <div>
                <dt>风格偏好</dt>
                <dd>{{ store.current.preferred_style || '未填写' }}</dd>
              </div>
              <div>
                <dt>核心卖点</dt>
                <dd>{{ store.current.core_selling_points || '未填写' }}</dd>
              </div>
            </div>
          </template>
        </section>

        <section class="panel panel-pad studio-section">
          <div class="section-head">
            <div>
              <p class="section-kicker">Analysis</p>
              <h2 class="section-title">商品分析</h2>
            </div>
            <el-button
              class="orange-button"
              type="primary"
              :disabled="!hasProject"
              :loading="runningAnalysis"
              @click="runWorkflow"
            >
              {{ store.current?.latest_analysis ? '重新分析并生成方案' : '运行分析与方案' }}
            </el-button>
          </div>

          <el-skeleton v-if="store.loading && hasProject" :rows="5" animated />
          <template v-else-if="store.current?.latest_analysis">
            <p class="analysis-lead">{{ store.current.latest_analysis.analysis.target_audience_analysis }}</p>
            <div class="tag-row">
              <el-tag v-for="item in store.current.latest_analysis.analysis.recommended_selling_points" :key="item">
                {{ item }}
              </el-tag>
            </div>
            <div class="analysis-grid">
              <div>
                <h3>推荐风格</h3>
                <ul>
                  <li v-for="item in store.current.latest_analysis.analysis.recommended_visual_styles" :key="item">
                    {{ item }}
                  </li>
                </ul>
              </div>
              <div>
                <h3>原图问题</h3>
                <ul>
                  <li v-for="item in store.current.latest_analysis.analysis.image_issues" :key="item">{{ item }}</li>
                </ul>
              </div>
            </div>
          </template>
          <el-empty v-else description="创建项目后，在这里运行商品分析并生成创意方案" />
        </section>

        <section class="panel panel-pad studio-section">
          <div class="section-head">
            <div>
              <p class="section-kicker">Creative routes</p>
              <h2 class="section-title">创意方案</h2>
            </div>
            <span v-if="store.current?.creative_plans.length" class="metric-pill">
              {{ store.current.creative_plans.length }} 个方向
            </span>
          </div>

          <div v-if="store.current?.creative_plans.length" class="plan-list">
            <article
              v-for="plan in store.current.creative_plans"
              :key="plan.id"
              class="plan-card"
              :class="{ selected: generatingPlanId === plan.id }"
            >
              <div>
                <span class="metric-pill">{{ plan.target_platform }}</span>
                <h3>{{ plan.plan_name }}</h3>
                <p>{{ plan.plan.visual_description }}</p>
              </div>
              <dl class="plan-details">
                <div>
                  <dt>主打卖点</dt>
                  <dd>{{ plan.plan.main_selling_point }}</dd>
                </div>
                <div>
                  <dt>推荐理由</dt>
                  <dd>{{ plan.plan.recommendation_reason }}</dd>
                </div>
                <div>
                  <dt>文案方向</dt>
                  <dd>{{ plan.plan.copywriting_direction }}</dd>
                </div>
              </dl>
              <el-button
                class="orange-button"
                type="primary"
                :loading="generatingPlanId === plan.id"
                @click="selectPlan(plan)"
              >
                选择并生成素材
              </el-button>
            </article>
          </div>
          <el-empty v-else description="分析完成后会在这里展示可选创意方案">
            <el-button v-if="hasProject" type="primary" :loading="runningAnalysis" @click="runWorkflow">
              生成创意方案
            </el-button>
          </el-empty>
        </section>

        <section class="panel panel-pad studio-section">
          <div class="section-head">
            <div>
              <p class="section-kicker">Generated assets</p>
              <h2 class="section-title">生成图片与评分</h2>
            </div>
            <span v-if="store.current?.generated_images.length" class="metric-pill accent">
              {{ store.current.generated_images.length }} 张图片
            </span>
          </div>

          <div v-if="store.current?.generated_images.length" class="image-grid">
            <article
              v-for="image in store.current.generated_images"
              :key="image.id"
              class="generated-card"
              :class="{ selected: selectedImageId === image.id }"
              @click="selectedImageId = image.id"
            >
              <div class="image-frame generated-frame">
                <img :src="assetUrl(image.image_url)" alt="生成图片" />
              </div>
              <div class="score-row">
                <strong>{{ image.score ? `${image.score} 分` : '待评分' }}</strong>
                <el-button text type="primary" @click.stop="review(image)">重新评分</el-button>
              </div>
            </article>
          </div>
          <el-empty v-else description="选择一个创意方案后，图片、评分和文案会连续生成" />
        </section>

        <section class="panel panel-pad studio-section">
          <div class="section-head">
            <div>
              <p class="section-kicker">Copy & revision</p>
              <h2 class="section-title">文案与自然语言修改</h2>
            </div>
          </div>

          <div class="copy-revision-grid">
            <div>
              <template v-if="store.current?.latest_copywriting">
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
              <el-empty v-else description="生成图片后会自动生成配套文案" />
            </div>

            <div class="revision-panel">
              <el-input
                v-model="instruction"
                type="textarea"
                :rows="4"
                placeholder="例如：背景更高级一点，商品再大一些，更适合小红书封面"
              />
              <el-button
                class="orange-button"
                type="primary"
                :disabled="!hasProject || !store.current?.generated_images.length"
                :loading="revising"
                @click="revise"
              >
                生成修改计划
              </el-button>
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
          </div>
        </section>

        <section class="panel panel-pad studio-section">
          <div class="section-head">
            <div>
              <p class="section-kicker">Agent Trace</p>
              <h2 class="section-title">流程诊断</h2>
            </div>
            <span v-if="store.current?.workflow_events.length" class="metric-pill">
              {{ store.current.workflow_events.length }} 条事件
            </span>
          </div>

          <el-collapse v-if="store.current?.workflow_events.length" class="trace-list">
            <el-collapse-item v-for="event in store.current.workflow_events" :key="event.id" :name="event.id">
              <template #title>
                <div class="trace-title">
                  <span class="status-dot" :class="event.status === 'failed' ? 'failed' : 'success'"></span>
                  <strong>{{ event.agent_name }}</strong>
                  <span>{{ event.summary }}</span>
                  <em>{{ event.latency_ms ?? 0 }}ms</em>
                </div>
              </template>
              <div class="trace-detail">
                <dl>
                  <div>
                    <dt>节点</dt>
                    <dd>{{ stepLabel(event.step_key) }}</dd>
                  </div>
                  <div>
                    <dt>状态</dt>
                    <dd>{{ event.status }}</dd>
                  </div>
                  <div>
                    <dt>时间</dt>
                    <dd>{{ formatDate(event.started_at) }}</dd>
                  </div>
                </dl>
                <el-alert v-if="event.error_message" type="error" :title="event.error_message" :closable="false" />
                <pre v-if="eventDetailText(event)">{{ eventDetailText(event) }}</pre>
              </div>
            </el-collapse-item>
          </el-collapse>
          <el-empty v-else description="运行分析、生成图片或修改后，会在这里沉淀可排查的 Agent 事件" />
        </section>
          </main>

          <aside class="studio-rail">
        <div class="panel panel-pad rail-card">
          <div class="rail-card-head">
            <div>
              <p class="section-kicker">Context</p>
              <h2 class="section-title">原图预览</h2>
            </div>
            <span v-if="store.current" class="metric-pill">{{ statusLabel(store.current.status) }}</span>
          </div>
          <div class="image-frame preview-frame">
            <img v-if="previewImageUrl" :src="previewImageUrl" alt="商品预览" />
            <div v-else class="empty-preview">
              <span>等待图片</span>
              <strong>上传后会贯穿整条生产线</strong>
            </div>
          </div>
        </div>

        <div v-if="selectedImage" class="panel panel-pad rail-card">
          <div class="rail-card-head">
            <div>
              <p class="section-kicker">Selected output</p>
              <h2 class="section-title">当前生成图</h2>
            </div>
            <span class="metric-pill accent">{{ selectedImage.score ? `${selectedImage.score} 分` : '待评分' }}</span>
          </div>
          <div class="image-frame output-preview-frame">
            <img :src="assetUrl(selectedImage.image_url)" alt="当前生成图" />
          </div>
        </div>

        <div v-if="hasProject" class="panel panel-pad rail-card next-card">
          <p class="section-kicker">Next action</p>
          <h2 class="section-title">{{ nextAction.title }}</h2>
          <p class="rail-copy">{{ nextAction.description }}</p>
          <el-button
            v-if="nextAction.kind === 'analysis'"
            class="orange-button"
            type="primary"
            :loading="runningAnalysis"
            @click="runWorkflow"
          >
            运行分析
          </el-button>
          <el-button
            v-else-if="nextAction.kind === 'plan'"
            class="orange-button"
            type="primary"
            :loading="generatingPlanId === store.current?.creative_plans[0]?.id"
            @click="generateFirstPlan"
          >
            生成素材
          </el-button>
          <div v-else class="export-actions">
            <el-button :href="markdownExportUrl(projectId)" tag="a" target="_blank">Markdown</el-button>
            <el-button :href="jsonExportUrl(projectId)" tag="a" target="_blank">JSON</el-button>
          </div>
        </div>
          </aside>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, type UploadFile } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import WorkflowStepper from '../components/WorkflowStepper.vue'
import { assetUrl, errorMessage } from '../api/client'
import {
  createProject,
  type CreativePlan,
  type GeneratedImage,
  jsonExportUrl,
  markdownExportUrl,
  reviseProject,
  type RevisionResponse,
  type WorkflowEvent,
  uploadAsset
} from '../api/productshot'
import { useProjectStore } from '../stores/project'

const route = useRoute()
const router = useRouter()
const store = useProjectStore()

const creating = ref(false)
const runningAnalysis = ref(false)
const generatingPlanId = ref<number | null>(null)
const revising = ref(false)
const selectedFile = ref<File | null>(null)
const localPreviewUrl = ref('')
const instruction = ref('')
const revision = ref<RevisionResponse | null>(null)
const selectedImageId = ref<number | null>(null)

const form = reactive({
  product_name: '',
  product_category: '',
  core_selling_points: '',
  target_platform: '小红书',
  target_audience: '',
  preferred_style: '小红书生活方式风'
})

const routeProjectId = computed(() => {
  const value = route.params.id
  return typeof value === 'string' ? Number(value) : 0
})
const projectId = computed(() => routeProjectId.value)
const hasProject = computed(() => Number.isFinite(projectId.value) && projectId.value > 0)
const primaryAsset = computed(() => store.current?.assets.find((asset) => asset.is_primary) || store.current?.assets[0])
const selectedImage = computed(
  () =>
    store.current?.generated_images.find((image) => image.id === selectedImageId.value) ||
    store.current?.generated_images[0]
)
const previewImageUrl = computed(() => {
  if (localPreviewUrl.value) return localPreviewUrl.value
  return primaryAsset.value ? assetUrl(primaryAsset.value.file_url) : ''
})
const pageTitle = computed(() => (hasProject.value ? store.current?.product_name || '项目工作台' : '创建商品营销项目'))
const pageDescription = computed(() =>
  hasProject.value
    ? '在同一个工作台里完成分析、方案、生成、评分、文案、修改和导出。'
    : '填写商品信息并上传原图，后续 Agent 会沿着同一条生产线连续推进。'
)
const nextAction = computed(() => {
  if (!store.current?.latest_analysis) {
    return { kind: 'analysis', title: '先理解商品', description: '运行商品分析后，系统会自动给出创意方案。' }
  }
  if (!store.current.generated_images.length) {
    return { kind: 'plan', title: '选择方案生成', description: '可以从创意方案里挑一个方向，连续生成图片、评分和文案。' }
  }
  return { kind: 'export', title: '素材包已成形', description: '继续修改，或直接导出 Markdown / JSON 素材报告。' }
})

onMounted(() => {
  loadFromRoute()
})

watch(
  () => route.params.id,
  () => {
    loadFromRoute()
  }
)

async function loadFromRoute() {
  revision.value = null
  instruction.value = ''
  if (!hasProject.value) {
    store.resetCurrent()
    selectedImageId.value = null
    return
  }
  localPreviewUrl.value = ''
  selectedFile.value = null
  try {
    await store.load(projectId.value)
    selectedImageId.value = store.current?.generated_images[0]?.id || null
  } catch (error) {
    ElMessage.error(errorMessage(error))
  }
}

function handleFile(file: UploadFile) {
  selectedFile.value = file.raw || null
  localPreviewUrl.value = selectedFile.value ? URL.createObjectURL(selectedFile.value) : ''
}

async function createStudioProject() {
  if (!form.product_name.trim()) {
    ElMessage.warning('请填写商品名称')
    return
  }
  if (!selectedFile.value) {
    ElMessage.warning('请上传商品图片')
    return
  }
  creating.value = true
  try {
    const project = await createProject(form)
    await uploadAsset(project.id, selectedFile.value)
    ElMessage.success('项目创建成功，已进入连续工作台')
    localPreviewUrl.value = ''
    selectedFile.value = null
    await router.replace(`/studio/${project.id}`)
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    creating.value = false
  }
}

async function runWorkflow() {
  if (!hasProject.value) return
  runningAnalysis.value = true
  try {
    await store.runAnalysisAndPlans(projectId.value)
    ElMessage.success('分析与创意方案已生成')
  } catch (error) {
    store.setStep('analysis', 'failed')
    ElMessage.error(errorMessage(error))
  } finally {
    runningAnalysis.value = false
  }
}

async function selectPlan(plan: CreativePlan) {
  if (!hasProject.value) return
  generatingPlanId.value = plan.id
  try {
    await store.generateFromPlan(projectId.value, plan)
    selectedImageId.value = store.current?.generated_images[0]?.id || null
    ElMessage.success('图片、评分和文案已生成')
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    generatingPlanId.value = null
  }
}

async function generateFirstPlan() {
  const plan = store.current?.creative_plans[0]
  if (plan) await selectPlan(plan)
}

async function review(image: GeneratedImage) {
  if (!hasProject.value) return
  try {
    await store.review(projectId.value, image)
    ElMessage.success('评分已更新')
  } catch (error) {
    ElMessage.error(errorMessage(error))
  }
}

async function revise() {
  if (!hasProject.value) return
  if (!instruction.value.trim()) {
    ElMessage.warning('请输入修改要求')
    return
  }
  revising.value = true
  try {
    revision.value = await reviseProject(projectId.value, instruction.value, selectedImage.value?.id)
    ElMessage.success('修改计划已生成')
    await store.load(projectId.value)
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    revising.value = false
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

function stepLabel(stepKey: string) {
  const labels: Record<string, string> = {
    analysis: '商品分析',
    plans: '创意策划',
    prompt: 'Prompt 构建',
    images: '图片生成',
    review: '图片评价',
    copy: '文案生成',
    revision: '修改计划'
  }
  return labels[stepKey] || stepKey
}

function formatDate(value: string) {
  return new Date(value).toLocaleString()
}

function eventDetailText(event: WorkflowEvent) {
  if (!event.detail_json) return ''
  try {
    const parsed = JSON.parse(event.detail_json)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return event.detail_json
  }
}
</script>

<style scoped>
.studio-page {
  max-width: 1540px;
}

.studio-header {
  align-items: flex-end;
  padding-bottom: 2px;
}

.studio-actions,
.export-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.studio-shell {
  min-width: 0;
}

.studio-workspace {
  min-width: 0;
}

.studio-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 330px);
  gap: 14px;
  margin-top: 14px;
  align-items: start;
}

.studio-main,
.brief-form,
.plan-list {
  display: grid;
  gap: 12px;
}

.studio-section {
  position: relative;
  scroll-margin-top: 24px;
}

.studio-section::before {
  position: absolute;
  top: 18px;
  left: -7px;
  width: 3px;
  height: 34px;
  border-radius: 999px;
  background: var(--ps-accent);
  content: "";
}

.studio-rail {
  position: sticky;
  top: 22px;
  display: grid;
  gap: 12px;
}

.section-head,
.score-row,
.rail-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.section-head .section-title,
.rail-card-head .section-title {
  margin-bottom: 0;
}

.form-grid,
.analysis-grid,
.copy-revision-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.upload-copy {
  padding: 22px 0 8px;
  color: var(--ps-primary);
  font-weight: 800;
}

.upload-subcopy {
  max-width: 380px;
  margin: 0 auto;
  color: var(--ps-muted);
  line-height: 1.65;
}

.brief-summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

dt {
  color: var(--ps-primary);
  font-size: 12px;
  font-weight: 800;
}

dd {
  margin: 5px 0 0;
  color: var(--ps-muted-strong);
  line-height: 1.65;
}

.analysis-lead {
  margin: 0 0 14px;
  color: var(--ps-muted-strong);
  line-height: 1.75;
}

.tag-row {
  margin-bottom: 10px;
}

.el-tag {
  margin: 0 7px 7px 0;
}

h3 {
  margin: 0 0 9px;
  color: var(--ps-heading);
  font-size: 17px;
}

ul {
  margin: 0;
  padding-left: 18px;
  color: var(--ps-muted);
  line-height: 1.72;
}

.plan-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(230px, 0.68fr) auto;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border: 1px solid var(--ps-border);
  border-radius: var(--ps-radius);
  background: var(--ps-surface-quiet);
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease,
    transform 160ms ease;
}

.plan-card:hover,
.plan-card.selected {
  border-color: rgba(201, 93, 66, 0.38);
  box-shadow: var(--ps-shadow-soft);
  transform: translateY(-1px);
}

.plan-card h3 {
  margin: 10px 0 8px;
  font-family: Georgia, "Times New Roman", "Songti SC", serif;
  font-size: 21px;
  font-weight: 650;
}

.plan-card p,
.plan-details {
  margin: 0;
  color: var(--ps-muted);
  line-height: 1.65;
}

.plan-details {
  display: grid;
  gap: 8px;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.generated-card {
  padding: 8px;
  border: 1px solid var(--ps-border);
  border-radius: var(--ps-radius);
  background: var(--ps-surface-quiet);
  cursor: pointer;
  transition:
    border-color 160ms ease,
    transform 160ms ease;
}

.generated-card:hover,
.generated-card.selected {
  border-color: var(--ps-accent);
  transform: translateY(-1px);
}

.generated-frame,
.output-preview-frame {
  aspect-ratio: 1 / 1;
}

.score-row {
  min-height: 38px;
  align-items: center;
}

.score-row strong {
  color: var(--ps-primary);
}

.copy-revision-grid p,
.revision-result p {
  color: var(--ps-muted);
  line-height: 1.75;
}

.revision-panel {
  display: grid;
  gap: 10px;
  align-content: start;
}

.revision-result {
  padding: 14px;
  border: 1px solid rgba(36, 88, 70, 0.14);
  border-radius: var(--ps-radius);
  background: var(--ps-surface-soft);
}

.preview-frame {
  min-height: 300px;
}

.empty-preview {
  display: grid;
  min-height: 300px;
  place-items: center;
  align-content: center;
  gap: 8px;
  padding: 20px;
  color: var(--ps-muted);
  text-align: center;
}

.empty-preview span {
  color: var(--ps-accent-dark);
  font-size: 12px;
  font-weight: 800;
}

.empty-preview strong {
  max-width: 220px;
  color: var(--ps-primary);
  font-family: Georgia, "Times New Roman", "Songti SC", serif;
  font-size: 22px;
  font-weight: 650;
  line-height: 1.18;
}

.rail-card {
  display: grid;
  gap: 11px;
}

.next-card {
  border-color: rgba(201, 93, 66, 0.24);
}

.rail-copy {
  margin: 0;
  color: var(--ps-muted);
  line-height: 1.65;
}

.trace-list {
  --el-collapse-header-bg-color: transparent;
  --el-collapse-content-bg-color: transparent;
  border-top: 1px solid var(--ps-border);
  border-bottom: 1px solid var(--ps-border);
}

.trace-title {
  display: grid;
  width: 100%;
  grid-template-columns: 12px minmax(100px, 0.24fr) minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding-right: 10px;
}

.trace-title span:not(.status-dot),
.trace-title em {
  min-width: 0;
  overflow: hidden;
  color: var(--ps-muted);
  font-size: 13px;
  font-style: normal;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trace-title strong {
  min-width: 0;
  overflow: hidden;
  color: var(--ps-heading);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trace-detail {
  display: grid;
  gap: 12px;
}

.trace-detail dl {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 0;
}

.trace-detail pre {
  max-height: 340px;
  margin: 0;
  overflow: auto;
  padding: 12px;
  border: 1px solid var(--ps-border);
  border-radius: var(--ps-radius);
  background: var(--ps-bg-ink);
  color: #fbfaf6;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
}

@media (max-width: 1040px) {
  .studio-grid,
  .plan-card {
    grid-template-columns: 1fr;
  }

  .studio-rail {
    position: static;
  }
}

@media (max-width: 760px) {
  .studio-header,
  .section-head,
  .rail-card-head {
    align-items: stretch;
    flex-direction: column;
  }

  .form-grid,
  .analysis-grid,
  .brief-summary,
  .copy-revision-grid,
  .image-grid,
  .trace-detail dl {
    grid-template-columns: 1fr;
  }

  .studio-section::before {
    display: none;
  }

  .trace-title {
    grid-template-columns: 12px minmax(0, 1fr) auto;
  }

  .trace-title span:not(.status-dot) {
    display: none;
  }
}
</style>
