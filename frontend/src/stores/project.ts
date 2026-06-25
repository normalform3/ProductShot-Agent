import { defineStore } from 'pinia'
import {
  analyzeProject,
  CreativePlan,
  generatePack,
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

export interface ProgressItem {
  key: string
  title: string
  detail: string
  status: StepStatus
}

let progressTimer: ReturnType<typeof setInterval> | null = null

export const useProjectStore = defineStore('project', {
  state: () => ({
    current: null as ProjectDetail | null,
    loading: false,
    progress: {
      active: false,
      percent: 0,
      message: '',
      items: [] as ProgressItem[]
    },
    steps: [
      { key: 'visual_analysis', title: '原图理解', status: 'pending', description: '提取商品外观与保真约束' },
      { key: 'analysis', title: '商品策略', status: 'pending', description: '理解卖点、人群与平台策略' },
      { key: 'plans', title: '方向规划', status: 'pending', description: '生成 3 个可选创意方向' },
      { key: 'prompt', title: 'Prompt Pack', status: 'pending', description: '只为选中方向构建提示词' },
      { key: 'images', title: '素材生成', status: 'pending', description: '参考原图生成当前方向素材' },
      { key: 'review', title: '质量评价', status: 'pending', description: '评分、排序并推荐最佳图' },
      { key: 'copy', title: '发布文案', status: 'pending', description: '输出多平台发布素材' },
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
    resetCurrent() {
      this.current = null
      this.lastReview = null
      this.stopProgress()
      this.steps.forEach((step) => {
        step.status = 'pending'
      })
    },
    async runAnalysisAndPlans(projectId: number) {
      this.startProgress()
      try {
        this.setStep('visual_analysis', 'running')
        this.setStep('analysis', 'running')
        this.markProgress('visual_analysis', 'running', '正在读取原图，提取商品外观、包装、材质和保真约束。', 8)
        this.beginSoftProgress(8, 56, [
          '多模态模型正在理解原图主体和背景问题。',
          '正在整理商品外观、颜色、材质和可见标签。',
          '正在形成后续图生图需要遵守的商品保真约束。'
        ])
        await analyzeProject(projectId)
        this.stopSoftProgress()
        this.markProgress('visual_analysis', 'success', '原图理解完成，已沉淀商品保真约束。', 58)
        this.markProgress('analysis', 'success', '商品策略完成，已提炼卖点、人群和平台方向。', 66)
        this.setStep('visual_analysis', 'success')
        this.setStep('analysis', 'success')

        this.setStep('plans', 'running')
        this.markProgress('plans', 'running', '正在规划 3 个可选营销方向。', 70)
        this.beginSoftProgress(70, 92, [
          '正在比较电商主图、社媒封面和促销海报方向。',
          '正在把卖点映射到画面场景、文案方向和预期产出。',
          '正在整理可供用户选择的 3 个创意方向。'
        ])
        await generatePlans(projectId)
        this.stopSoftProgress()
        this.markProgress('plans', 'success', '3 个创意方向已生成，等待用户选择。', 96)
        this.setStep('plans', 'success')
        await this.load(projectId)
        this.finishProgress('规划完成，可以选择一个方向生成素材。')
      } catch (error) {
        this.stopSoftProgress()
        this.markRunningProgressFailed()
        throw error
      }
    },
    async generateFromPlan(projectId: number, plan: CreativePlan) {
      this.setStep('prompt', 'running')
      this.setStep('images', 'running')
      const result = await generatePack(projectId, plan.id, 4)
      this.setStep('prompt', 'success')
      this.setStep('images', 'success')
      const first = result.images.find((image) => image.is_recommended) || result.images[0]
      if (first) {
        this.setStep('review', 'success')
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
    startProgress() {
      this.stopSoftProgress()
      this.progress = {
        active: true,
        percent: 4,
        message: '准备启动 Agent 工作流。',
        items: [
          { key: 'visual_analysis', title: '原图理解', detail: '等待多模态模型读取原图。', status: 'pending' },
          { key: 'analysis', title: '商品策略', detail: '等待结合商品信息生成策略。', status: 'pending' },
          { key: 'plans', title: '方向规划', detail: '等待生成 3 个可选创意方向。', status: 'pending' }
        ]
      }
    },
    beginSoftProgress(start: number, max: number, messages: string[]) {
      this.stopSoftProgress()
      let index = 0
      this.progress.percent = Math.max(this.progress.percent, start)
      this.progress.message = messages[0]
      progressTimer = setInterval(() => {
        if (!this.progress.active) return
        index = (index + 1) % messages.length
        this.progress.message = messages[index]
        if (this.progress.percent < max) {
          this.progress.percent += this.progress.percent < max - 10 ? 3 : 1
        }
      }, 1800)
    },
    stopSoftProgress() {
      if (progressTimer) {
        clearInterval(progressTimer)
        progressTimer = null
      }
    },
    markProgress(key: string, status: StepStatus, detail: string, percent: number) {
      const item = this.progress.items.find((entry) => entry.key === key)
      if (item) {
        item.status = status
        item.detail = detail
      }
      this.progress.active = true
      this.progress.percent = Math.max(this.progress.percent, percent)
      this.progress.message = detail
    },
    finishProgress(message: string) {
      this.stopSoftProgress()
      this.progress.percent = 100
      this.progress.message = message
      window.setTimeout(() => {
        this.progress.active = false
      }, 900)
    },
    stopProgress() {
      this.stopSoftProgress()
      this.progress.active = false
      this.progress.percent = 0
      this.progress.message = ''
      this.progress.items = []
    },
    markRunningProgressFailed() {
      const running = this.progress.items.find((item) => item.status === 'running')
      if (running) {
        running.status = 'failed'
        running.detail = '当前步骤没有按预期完成，请查看错误提示或流程诊断。'
      }
      this.progress.message = '当前步骤失败，请查看错误提示。'
    },
    syncSteps() {
      const status = this.current?.status
      const rank: Record<string, number> = {
        draft: 0,
        analyzed: 2,
        planned: 3,
        generated: 5,
        reviewed: 6,
        copywritten: 7,
        revised: 6,
        exported: 8
      }
      const done = rank[status || 'draft'] || 0
      this.steps.forEach((step, index) => {
        step.status = index < done ? 'success' : 'pending'
      })
    }
  }
})
