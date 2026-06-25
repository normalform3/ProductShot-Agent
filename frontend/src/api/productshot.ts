import { http } from './client'

export interface Project {
  id: number
  product_name: string
  product_category?: string | null
  core_selling_points?: string | null
  target_platform: string
  target_audience?: string | null
  preferred_style?: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  product_name: string
  product_category?: string
  core_selling_points?: string
  target_platform: string
  target_audience?: string
  preferred_style?: string
}

export interface ProductAsset {
  id: number
  project_id: number
  file_url: string
  file_path: string
  file_type: string
  is_primary: boolean
  width?: number | null
  height?: number | null
  created_at: string
}

export interface ProductAnalysis {
  product_type: string
  core_features: string[]
  target_audience_analysis: string
  recommended_selling_points: string[]
  recommended_visual_styles: string[]
  image_issues: string[]
  marketing_angles: string[]
  visual_summary?: string | null
  product_consistency_rules: string[]
  platform_strategy?: string | null
}

export interface VisualAnalysis {
  product_appearance: string
  dominant_colors: string[]
  materials: string[]
  visible_text_or_logo: string[]
  subject_clarity: string
  background_issues: string[]
  fidelity_constraints: string[]
  marketing_opportunities: string[]
}

export interface ProductVisualAnalysisRead {
  id: number
  project_id: number
  analysis: VisualAnalysis
  created_at: string
}

export interface ProductAnalysisRead {
  id: number
  project_id: number
  analysis: ProductAnalysis
  created_at: string
}

export interface CreativePlanPayload {
  plan_name: string
  applicable_platform: string
  visual_description: string
  background_scene: string
  visual_style: string
  main_selling_point: string
  recommendation_reason: string
  copywriting_direction: string
  expected_outputs: string[]
}

export interface CreativePlan {
  id: number
  project_id: number
  plan_name: string
  plan_description: string
  target_platform: string
  visual_style: string
  selling_angle: string
  plan: CreativePlanPayload
  created_at: string
}

export interface PromptPayload {
  positive_prompt: string
  negative_prompt: string
  size: string
  style: string
  product_consistency_notes: string
}

export interface PromptPackPayload extends PromptPayload {
  platform: string
  generation_mode: string
  reference_strength: number
  consistency_rules: string[]
}

export interface GenerationTask {
  id: number
  project_id: number
  plan_id?: number | null
  prompt: string
  negative_prompt: string
  model_name: string
  status: string
  error_message?: string | null
  created_at: string
  updated_at: string
}

export interface GeneratedImage {
  id: number
  task_id: number
  project_id: number
  plan_id?: number | null
  platform?: string | null
  generation_mode?: string | null
  prompt_pack_id?: string | null
  image_url: string
  image_path: string
  width?: number | null
  height?: number | null
  score?: number | null
  is_selected: boolean
  is_recommended: boolean
  created_at: string
}

export interface GeneratedImagesResponse {
  task: GenerationTask
  prompt: PromptPackPayload
  images: GeneratedImage[]
}

export interface ImageReviewPayload {
  overall_score: number
  product_clarity: number
  product_consistency: number
  style_match: number
  commercial_value: number
  platform_fit: number
  text_artifact_risk: string
  ai_artifact_risk: string
  recommendation_level: string
  defects: string[]
  suggestions: string[]
}

export interface ImageReviewRead {
  id: number
  image_id: number
  review: ImageReviewPayload
  created_at: string
}

export interface CopywritingPayload {
  title: string
  selling_points: string[]
  xiaohongshu_title: string
  xiaohongshu_text: string
  moments_text: string
  taobao_text: string
  douyin_script: string
  tags: string[]
}

export interface CopywritingRead {
  id: number
  project_id: number
  image_id?: number | null
  copywriting: CopywritingPayload
  created_at: string
}

export interface RevisionResponse {
  revision_type: string
  target: string
  modification_plan: string[]
  new_prompt: PromptPayload
  should_regenerate: boolean
  notes: string
}

export interface ModelSettings {
  text_provider: string
  text_model: string
  image_provider: string
  image_model: string
  dashscope_text_base_url: string
  dashscope_image_generation_url: string
  dashscope_workspace_id_configured: boolean
  dashscope_api_key_configured: boolean
  available_text_providers: string[]
  available_image_providers: string[]
}

export type ModelSettingsUpdate = Partial<
  Pick<
    ModelSettings,
    | 'text_provider'
    | 'text_model'
    | 'image_provider'
    | 'image_model'
    | 'dashscope_text_base_url'
    | 'dashscope_image_generation_url'
  >
>

export interface ModelConnectionTest {
  provider: string
  model: string
  status: string
  latency_ms: number
  message: string
  checked_at: string
}

export interface WorkflowEvent {
  id: number
  project_id: number
  step_key: string
  agent_name: string
  status: string
  summary: string
  detail_json: string
  error_message?: string | null
  started_at: string
  ended_at?: string | null
  latency_ms?: number | null
}

export interface ProjectDetail extends Project {
  assets: ProductAsset[]
  visual_analysis?: ProductVisualAnalysisRead | null
  product_strategy?: ProductAnalysisRead | null
  latest_analysis?: ProductAnalysisRead | null
  creative_plans: CreativePlan[]
  generated_images: GeneratedImage[]
  latest_copywriting?: CopywritingRead | null
  workflow_events: WorkflowEvent[]
}

export async function createProject(payload: ProjectCreate) {
  const { data } = await http.post<Project>('/api/projects', payload)
  return data
}

export async function listProjects() {
  const { data } = await http.get<Project[]>('/api/projects')
  return data
}

export async function getProject(projectId: number) {
  const { data } = await http.get<ProjectDetail>(`/api/projects/${projectId}`)
  return data
}

export async function uploadAsset(projectId: number, file: File) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await http.post<ProductAsset>(`/api/projects/${projectId}/assets`, form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return data
}

export async function analyzeProject(projectId: number) {
  const { data } = await http.post<ProductAnalysisRead>(`/api/projects/${projectId}/agent/analyze`)
  return data
}

export async function generatePlans(projectId: number) {
  const { data } = await http.post<CreativePlan[]>(`/api/projects/${projectId}/agent/generate-plans`)
  return data
}

export async function planProject(projectId: number) {
  const { data } = await http.post<CreativePlan[]>(`/api/projects/${projectId}/agent/plan`)
  return data
}

export async function listPlans(projectId: number) {
  const { data } = await http.get<CreativePlan[]>(`/api/projects/${projectId}/creative-plans`)
  return data
}

export async function generateImages(projectId: number, planId: number, count = 4) {
  const { data } = await http.post<GeneratedImagesResponse>(
    `/api/projects/${projectId}/creative-plans/${planId}/generate-images`,
    { count }
  )
  return data
}

export async function generatePack(projectId: number, planId: number, count = 4) {
  const { data } = await http.post<GeneratedImagesResponse>(
    `/api/projects/${projectId}/creative-plans/${planId}/generate-pack`,
    { count }
  )
  return data
}

export async function reviewImage(projectId: number, imageId: number) {
  const { data } = await http.post<ImageReviewRead>(`/api/projects/${projectId}/generated-images/${imageId}/review`)
  return data
}

export async function createCopywriting(projectId: number, imageId?: number) {
  const { data } = await http.post<CopywritingRead>(`/api/projects/${projectId}/copywriting`, {
    image_id: imageId
  })
  return data
}

export async function reviseProject(projectId: number, instruction: string, imageId?: number) {
  const { data } = await http.post<RevisionResponse>(`/api/projects/${projectId}/revise`, {
    target_image_id: imageId,
    instruction
  })
  return data
}

export async function getModelSettings() {
  const { data } = await http.get<ModelSettings>('/api/model-settings')
  return data
}

export async function updateModelSettings(payload: ModelSettingsUpdate) {
  const { data } = await http.put<ModelSettings>('/api/model-settings', payload)
  return data
}

export async function testTextModelConnection() {
  const { data } = await http.post<ModelConnectionTest>('/api/model-settings/test-text')
  return data
}

export function markdownExportUrl(projectId: number) {
  return `${http.defaults.baseURL}/api/projects/${projectId}/export/markdown`
}

export function jsonExportUrl(projectId: number) {
  return `${http.defaults.baseURL}/api/projects/${projectId}/export/json`
}
