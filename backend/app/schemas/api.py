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


class ProductAnalysisPayload(BaseModel):
    product_type: str
    core_features: list[str]
    target_audience_analysis: str
    recommended_selling_points: list[str]
    recommended_visual_styles: list[str]
    image_issues: list[str]
    marketing_angles: list[str]


class ProductAnalysisRead(BaseModel):
    id: int
    project_id: int
    analysis: ProductAnalysisPayload
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
    image_url: str
    image_path: str
    width: int | None
    height: int | None
    score: float | None
    is_selected: bool
    created_at: datetime


class GeneratedImagesResponse(BaseModel):
    task: GenerationTaskRead
    prompt: PromptPayload
    images: list[GeneratedImageRead]


class ImageReviewPayload(BaseModel):
    overall_score: int
    product_clarity: int
    style_match: int
    commercial_value: int
    platform_fit: int
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


class RevisionResponse(BaseModel):
    revision_type: str
    target: str
    modification_plan: list[str]
    new_prompt: PromptPayload
    should_regenerate: bool
    notes: str


class ProjectDetail(ProjectRead):
    assets: list[ProductAssetRead]
    latest_analysis: ProductAnalysisRead | None
    creative_plans: list[CreativePlanRead]
    generated_images: list[GeneratedImageRead]
    latest_copywriting: CopywritingRead | None


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
