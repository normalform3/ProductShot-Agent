<template>
  <section class="page">
    <div class="page-header">
      <div>
        <span class="eyebrow">Agent Pipeline</span>
        <h1 class="page-title">Agent 工作流</h1>
        <p class="page-description">从商品分析到创意方案，展示多 Agent 如何把一张普通商品图变成内容生产流程。</p>
      </div>
      <el-button class="orange-button" type="primary" size="large" :loading="running" @click="runWorkflow">
        运行商品分析
      </el-button>
    </div>

    <WorkflowStepper :steps="store.steps" />

    <div class="grid-2 workflow-body">
      <div class="panel panel-pad">
        <div class="section-headline">
          <p class="section-kicker">Analysis</p>
          <h2 class="section-title">商品分析结果</h2>
        </div>
        <el-skeleton v-if="store.loading" :rows="6" animated />
        <template v-else-if="store.current?.latest_analysis">
          <p class="analysis-lead">{{ store.current.latest_analysis.analysis.target_audience_analysis }}</p>
          <div class="tag-row">
            <el-tag v-for="item in store.current.latest_analysis.analysis.recommended_selling_points" :key="item">
              {{ item }}
            </el-tag>
          </div>
          <h3>原图问题</h3>
          <ul>
            <li v-for="item in store.current.latest_analysis.analysis.image_issues" :key="item">{{ item }}</li>
          </ul>
        </template>
        <el-empty v-else description="尚未运行商品分析" />
      </div>

      <div class="panel panel-pad">
        <div class="section-headline">
          <p class="section-kicker">Creative routes</p>
          <h2 class="section-title">创意方案预览</h2>
        </div>
        <div v-if="store.current?.creative_plans.length" class="mini-plans">
          <article v-for="plan in store.current.creative_plans" :key="plan.id" class="mini-plan">
            <span class="metric-pill">{{ plan.target_platform }}</span>
            <strong>{{ plan.plan_name }}</strong>
            <p>{{ plan.plan.recommendation_reason }}</p>
          </article>
          <el-button type="primary" @click="$router.push(`/plans/${id}`)">选择方案并生成图片</el-button>
        </div>
        <el-empty v-else description="生成创意方案后会显示在这里" />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import WorkflowStepper from '../components/WorkflowStepper.vue'
import { useProjectStore } from '../stores/project'
import { errorMessage } from '../api/client'

const props = defineProps<{ id: string }>()
const id = Number(props.id)
const store = useProjectStore()
const running = ref(false)

onMounted(() => store.load(id))

async function runWorkflow() {
  running.value = true
  try {
    await store.runAnalysisAndPlans(id)
    ElMessage.success('Agent 工作流已生成创意方案')
  } catch (error) {
    store.setStep('analysis', 'failed')
    ElMessage.error(errorMessage(error))
  } finally {
    running.value = false
  }
}
</script>

<style scoped>
.workflow-body {
  margin-top: 18px;
}

.section-headline {
  margin-bottom: 12px;
}

.analysis-lead {
  margin: 0 0 16px;
  color: var(--ps-muted-strong);
  line-height: 1.8;
}

.tag-row {
  margin-bottom: 16px;
}

.el-tag {
  margin: 0 8px 8px 0;
}

h3 {
  margin: 20px 0 8px;
  color: var(--ps-heading);
}

ul {
  margin: 0;
  padding-left: 20px;
  color: var(--ps-muted);
  line-height: 1.8;
}

.mini-plans {
  display: grid;
  gap: 12px;
}

.mini-plan {
  display: grid;
  gap: 10px;
  padding: 16px;
  border: 1px solid var(--ps-border);
  border-radius: var(--ps-radius);
  background: var(--ps-surface-quiet);
}

.mini-plan strong {
  color: var(--ps-heading);
  font-size: 17px;
}

.mini-plan p {
  margin: 0;
  color: var(--ps-muted);
  line-height: 1.7;
}
</style>
