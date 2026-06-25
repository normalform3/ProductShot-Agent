from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=160)
    product_category: str | None = None
    core_selling_points: str | None = None
    target_platform: str = Field(min_length=1, max_length=80)
    target_audience: str | None = None
    preferred_style: str | None = None


class ProjectRead(ProjectCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
    updated_at: datetime


class ProductAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    file_url: str
    file_path: str
    file_type: str
    is_primary: bool
    width: int | None
    height: int | None
    created_at: datetime


class VisualAnalysisPayload(BaseModel):
    product_appearance: str
    dominant_colors: list[str]
    materials: list[str]
    visible_text_or_logo: list[str]
    subject_clarity: str
    background_issues: list[str]
    fidelity_constraints: list[str]
    marketing_opportunities: list[str]


class ProductStrategyPayload(BaseModel):
    product_type: str
    core_features: list[str]
    target_audience_analysis: str
    recommended_selling_points: list[str]
    recommended_visual_styles: list[str]
    image_issues: list[str]
    marketing_angles: list[str]
    visual_summary: str | None = None
    product_consistency_rules: list[str] = Field(default_factory=list)
    platform_strategy: str | None = None


ProductAnalysisPayload = ProductStrategyPayload


class ProductVisualAnalysisRead(BaseModel):
    id: int
    project_id: int
    analysis: VisualAnalysisPayload
    created_at: datetime


class ProductAnalysisRead(BaseModel):
    id: int
    project_id: int
    analysis: ProductStrategyPayload
    created_at: datetime


class CreativePlanPayload(BaseModel):
    plan_name: str
    applicable_platform: str
    visual_description: str
    background_scene: str
    visual_style: str
    main_selling_point: str
    recommendation_reason: str
    copywriting_direction: str
    expected_outputs: list[str] = Field(default_factory=list)


class CreativePlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    plan_name: str
    plan_description: str
    target_platform: str
    visual_style: str
    selling_angle: str
    plan: CreativePlanPayload
    created_at: datetime


class PromptPayload(BaseModel):
    positive_prompt: str
    negative_prompt: str
    size: str
    style: str
    product_consistency_notes: str


class PromptPackPayload(PromptPayload):
    platform: str
    generation_mode: str
    reference_strength: float = Field(default=0.72, ge=0, le=1)
    consistency_rules: list[str] = Field(default_factory=list)


class GenerateImagesRequest(BaseModel):
    count: int = Field(default=4, ge=1, le=6)


class GenerationTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    plan_id: int | None
    prompt: str
    negative_prompt: str
    model_name: str
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class GeneratedImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    project_id: int
    plan_id: int | None = None
    platform: str | None = None
    generation_mode: str | None = None
    prompt_pack_id: str | None = None
    image_url: str
    image_path: str
    width: int | None
    height: int | None
    score: float | None
    is_selected: bool
    is_recommended: bool = False
    created_at: datetime


class GeneratedImagesResponse(BaseModel):
    task: GenerationTaskRead
    prompt: PromptPackPayload
    images: list[GeneratedImageRead]


class ImageReviewPayload(BaseModel):
    overall_score: int
    product_clarity: int
    product_consistency: int = 80
    style_match: int
    commercial_value: int
    platform_fit: int
    text_artifact_risk: str = "low"
    ai_artifact_risk: str = "low"
    recommendation_level: str = "usable"
    defects: list[str]
    suggestions: list[str]


class ImageReviewRead(BaseModel):
    id: int
    image_id: int
    review: ImageReviewPayload
    created_at: datetime


class CopywritingRequest(BaseModel):
    image_id: int | None = None


class CopywritingPayload(BaseModel):
    title: str
    selling_points: list[str]
    xiaohongshu_title: str
    xiaohongshu_text: str
    moments_text: str
    taobao_text: str
    douyin_script: str = ""
    tags: list[str]


class CopywritingRead(BaseModel):
    id: int
    project_id: int
    image_id: int | None
    copywriting: CopywritingPayload
    created_at: datetime


class RevisionRequest(BaseModel):
    target_image_id: int | None = None
    instruction: str = Field(min_length=1)


class ModelSettingsRead(BaseModel):
    text_provider: str
    text_model: str
    image_provider: str
    image_model: str
    dashscope_text_base_url: str
    dashscope_image_generation_url: str
    dashscope_workspace_id_configured: bool
    dashscope_api_key_configured: bool
    available_text_providers: list[str]
    available_image_providers: list[str]


class ModelSettingsUpdate(BaseModel):
    text_provider: str | None = Field(default=None, max_length=40)
    text_model: str | None = Field(default=None, max_length=120)
    image_provider: str | None = Field(default=None, max_length=40)
    image_model: str | None = Field(default=None, max_length=120)
    dashscope_text_base_url: str | None = Field(default=None, max_length=300)
    dashscope_image_generation_url: str | None = Field(default=None, max_length=300)


class ModelConnectionTestRead(BaseModel):
    provider: str
    model: str
    status: str
    latency_ms: int
    message: str
    checked_at: datetime


class RevisionResponse(BaseModel):
    revision_type: str
    target: str
    modification_plan: list[str]
    new_prompt: PromptPackPayload
    should_regenerate: bool
    notes: str


class WorkflowEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    step_key: str
    agent_name: str
    status: str
    summary: str
    detail_json: str
    error_message: str | None
    started_at: datetime
    ended_at: datetime | None
    latency_ms: int | None


class ProjectDetail(ProjectRead):
    assets: list[ProductAssetRead]
    visual_analysis: ProductVisualAnalysisRead | None = None
    product_strategy: ProductAnalysisRead | None = None
    latest_analysis: ProductAnalysisRead | None
    creative_plans: list[CreativePlanRead]
    generated_images: list[GeneratedImageRead]
    latest_copywriting: CopywritingRead | None
    workflow_events: list[WorkflowEventRead]


class ExportReport(BaseModel):
    project: ProjectRead
    assets: list[ProductAssetRead]
    analysis: ProductAnalysisPayload | None
    creative_plans: list[CreativePlanRead]
    generation_tasks: list[GenerationTaskRead]
    generated_images: list[GeneratedImageRead]
    image_reviews: list[ImageReviewRead]
    copywriting: list[CopywritingRead]
    revision: RevisionResponse | None = None
    metadata: dict[str, Any]
