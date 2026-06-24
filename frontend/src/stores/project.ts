import { defineStore } from 'pinia'
import {
  analyzeProject,
  createCopywriting,
  CreativePlan,
  generateImages,
  generatePlans,
  GeneratedImage,
  getProject,
  ImageReviewRead,
  ProjectDetail,
  reviewImage
} from '../api/productshot'

export type StepStatus = 'pending' | 'running' | 'success' | 'failed'

export interface WorkflowStep {
  key: string
  title: string
  status: StepStatus
  description: string
}

export const useProjectStore = defineStore('project', {
  state: () => ({
    current: null as ProjectDetail | null,
    loading: false,
    steps: [
      { key: 'analysis', title: '商品分析', status: 'pending', description: '理解商品、卖点与原图问题' },
      { key: 'plans', title: '创意策划', status: 'pending', description: '生成 3 个营销创意方案' },
      { key: 'prompt', title: 'Prompt 构建', status: 'pending', description: '生成商品保真提示词' },
      { key: 'images', title: '图片生成', status: 'pending', description: '调用 Mock ImageProvider' },
      { key: 'review', title: '图片评价', status: 'pending', description: '评分与优化建议' },
      { key: 'copy', title: '文案生成', status: 'pending', description: '输出多平台文案' },
      { key: 'export', title: '导出素材', status: 'pending', description: 'Markdown / JSON 报告' }
    ] as WorkflowStep[],
    lastReview: null as ImageReviewRead | null
  }),
  actions: {
    async load(projectId: number) {
      this.loading = true
      try {
        this.current = await getProject(projectId)
        this.syncSteps()
      } finally {
        this.loading = false
      }
    },
    async runAnalysisAndPlans(projectId: number) {
      this.setStep('analysis', 'running')
      await analyzeProject(projectId)
      this.setStep('analysis', 'success')
      this.setStep('plans', 'running')
      await generatePlans(projectId)
      this.setStep('plans', 'success')
      await this.load(projectId)
    },
    async generateFromPlan(projectId: number, plan: CreativePlan) {
      this.setStep('prompt', 'running')
      this.setStep('images', 'running')
      const result = await generateImages(projectId, plan.id, 4)
      this.setStep('prompt', 'success')
      this.setStep('images', 'success')
      const first = result.images[0]
      if (first) {
        this.setStep('review', 'running')
        this.lastReview = await reviewImage(projectId, first.id)
        this.setStep('review', 'success')
        this.setStep('copy', 'running')
        await createCopywriting(projectId, first.id)
        this.setStep('copy', 'success')
      }
      await this.load(projectId)
      return result
    },
    async review(projectId: number, image: GeneratedImage) {
      this.setStep('review', 'running')
      this.lastReview = await reviewImage(projectId, image.id)
      this.setStep('review', 'success')
      await this.load(projectId)
    },
    setStep(key: string, status: StepStatus) {
      const item = this.steps.find((step) => step.key === key)
      if (item) item.status = status
    },
    syncSteps() {
      const status = this.current?.status
      const rank: Record<string, number> = {
        draft: 0,
        analyzed: 1,
        planned: 2,
        generated: 4,
        reviewed: 5,
        copywritten: 6,
        revised: 6,
        exported: 7
      }
      const done = rank[status || 'draft'] || 0
      this.steps.forEach((step, index) => {
        step.status = index < done ? 'success' : 'pending'
      })
    }
  }
})

