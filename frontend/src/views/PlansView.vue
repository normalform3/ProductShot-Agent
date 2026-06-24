<template>
  <section class="page">
    <div class="page-header">
      <div>
        <span class="eyebrow">Creative Direction</span>
        <h1 class="page-title">创意方案</h1>
        <p class="page-description">选择一个画面方向，系统会生成 Prompt、Mock 图片、评分和配套文案。</p>
      </div>
      <el-button @click="$router.push(`/workflow/${id}`)">返回工作流</el-button>
    </div>

    <div v-if="loading" class="panel panel-pad">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="plans.length" class="grid-3">
      <article v-for="plan in plans" :key="plan.id" class="plan-card panel panel-pad">
        <div>
          <span class="metric-pill">{{ plan.target_platform }}</span>
          <h2>{{ plan.plan_name }}</h2>
          <p class="visual-copy">{{ plan.plan.visual_description }}</p>
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
        <el-button class="orange-button" type="primary" :loading="generatingId === plan.id" @click="selectPlan(plan)">
          选择并生成
        </el-button>
      </article>
    </div>

    <el-empty v-else description="还没有创意方案，请先运行 Agent 工作流">
      <el-button type="primary" @click="$router.push(`/workflow/${id}`)">去生成方案</el-button>
    </el-empty>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { CreativePlan, listPlans } from '../api/productshot'
import { errorMessage } from '../api/client'
import { useProjectStore } from '../stores/project'

const props = defineProps<{ id: string }>()
const id = Number(props.id)
const router = useRouter()
const store = useProjectStore()
const plans = ref<CreativePlan[]>([])
const loading = ref(false)
const generatingId = ref<number | null>(null)

onMounted(load)

async function load() {
  loading.value = true
  try {
    plans.value = await listPlans(id)
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    loading.value = false
  }
}

async function selectPlan(plan: CreativePlan) {
  generatingId.value = plan.id
  try {
    await store.generateFromPlan(id, plan)
    ElMessage.success('图片、评分和文案已生成')
    router.push(`/results/${id}`)
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    generatingId.value = null
  }
}
</script>

<style scoped>
.plan-card {
  display: flex;
  min-height: 460px;
  flex-direction: column;
  justify-content: space-between;
  transition:
    border-color 160ms ease,
    transform 160ms ease,
    box-shadow 160ms ease;
}

.plan-card:hover {
  border-color: rgba(229, 111, 79, 0.4);
  box-shadow: var(--ps-shadow);
  transform: translateY(-2px);
}

.plan-card h2 {
  margin: 18px 0 10px;
  color: var(--ps-heading);
  font-family: Georgia, "Times New Roman", "Songti SC", serif;
  font-size: 28px;
  font-weight: 650;
  line-height: 1.16;
}

.visual-copy,
dd {
  color: var(--ps-muted);
  line-height: 1.7;
}

.visual-copy {
  margin: 0;
}

.plan-details {
  display: grid;
  gap: 12px;
  margin: 18px 0;
}

dt {
  color: var(--ps-primary);
  font-size: 12px;
  font-weight: 800;
}

dd {
  margin: 5px 0 0;
}
</style>
