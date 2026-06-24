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
  image_url: string
  image_path: string
  width?: number | null
  height?: number | null
  score?: number | null
  is_selected: boolean
  created_at: string
}

export interface GeneratedImagesResponse {
  task: GenerationTask
  prompt: PromptPayload
  images: GeneratedImage[]
}

export interface ImageReviewPayload {
  overall_score: number
  product_clarity: number
  style_match: number
  commercial_value: number
  platform_fit: number
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

export interface ProjectDetail extends Project {
  assets: ProductAsset[]
  latest_analysis?: ProductAnalysisRead | null
  creative_plans: CreativePlan[]
  generated_images: GeneratedImage[]
  latest_copywriting?: CopywritingRead | null
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

export function markdownExportUrl(projectId: number) {
  return `${http.defaults.baseURL}/api/projects/${projectId}/export/markdown`
}

export function jsonExportUrl(projectId: number) {
  return `${http.defaults.baseURL}/api/projects/${projectId}/export/json`
}

