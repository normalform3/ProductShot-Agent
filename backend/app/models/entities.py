from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_name: Mapped[str] = mapped_column(String(160), nullable=False)
    product_category: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    core_selling_points: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_platform: Mapped[str] = mapped_column(String(80), nullable=False)
    target_audience: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    preferred_style: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    assets: Mapped[list["ProductAsset"]] = relationship(cascade="all, delete-orphan", back_populates="project")
    analyses: Mapped[list["ProductAnalysis"]] = relationship(cascade="all, delete-orphan", back_populates="project")
    visual_analyses: Mapped[list["ProductVisualAnalysis"]] = relationship(cascade="all, delete-orphan", back_populates="project")
    creative_plans: Mapped[list["CreativePlan"]] = relationship(cascade="all, delete-orphan", back_populates="project")
    generation_tasks: Mapped[list["GenerationTask"]] = relationship(cascade="all, delete-orphan", back_populates="project")
    generated_images: Mapped[list["GeneratedImage"]] = relationship(cascade="all, delete-orphan", back_populates="project")
    copywriting_items: Mapped[list["Copywriting"]] = relationship(cascade="all, delete-orphan", back_populates="project")
    workflow_events: Mapped[list["WorkflowEvent"]] = relationship(cascade="all, delete-orphan", back_populates="project")


class ProductAsset(Base):
    __tablename__ = "product_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(80), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    project: Mapped[Project] = relationship(back_populates="assets")


class ProductAnalysis(Base):
    __tablename__ = "product_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    analysis_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    project: Mapped[Project] = relationship(back_populates="analyses")


class ProductVisualAnalysis(Base):
    __tablename__ = "product_visual_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    analysis_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    project: Mapped[Project] = relationship(back_populates="visual_analyses")


class CreativePlan(Base):
    __tablename__ = "creative_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    plan_name: Mapped[str] = mapped_column(String(160), nullable=False)
    plan_description: Mapped[str] = mapped_column(Text, nullable=False)
    target_platform: Mapped[str] = mapped_column(String(80), nullable=False)
    visual_style: Mapped[str] = mapped_column(String(160), nullable=False)
    selling_angle: Mapped[str] = mapped_column(String(200), nullable=False)
    plan_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    project: Mapped[Project] = relationship(back_populates="creative_plans")
    generation_tasks: Mapped[list["GenerationTask"]] = relationship(cascade="all, delete-orphan", back_populates="plan")


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    plan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("creative_plans.id"), nullable=True, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    negative_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    project: Mapped[Project] = relationship(back_populates="generation_tasks")
    plan: Mapped[Optional[CreativePlan]] = relationship(back_populates="generation_tasks")
    images: Mapped[list["GeneratedImage"]] = relationship(cascade="all, delete-orphan", back_populates="task")


class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("generation_tasks.id"), nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    plan_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    platform: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    generation_mode: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    prompt_pack_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    prompt_pack_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    task: Mapped[GenerationTask] = relationship(back_populates="images")
    project: Mapped[Project] = relationship(back_populates="generated_images")
    reviews: Mapped[list["ImageReview"]] = relationship(cascade="all, delete-orphan", back_populates="image")
    copywriting_items: Mapped[list["Copywriting"]] = relationship(cascade="all, delete-orphan", back_populates="image")


class ImageReview(Base):
    __tablename__ = "image_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("generated_images.id"), nullable=False, index=True)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    product_clarity_score: Mapped[int] = mapped_column(Integer, nullable=False)
    product_consistency_score: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    style_match_score: Mapped[int] = mapped_column(Integer, nullable=False)
    commercial_value_score: Mapped[int] = mapped_column(Integer, nullable=False)
    platform_fit_score: Mapped[int] = mapped_column(Integer, nullable=False)
    text_artifact_risk: Mapped[str] = mapped_column(String(40), default="low", nullable=False)
    ai_artifact_risk: Mapped[str] = mapped_column(String(40), default="low", nullable=False)
    recommendation_level: Mapped[str] = mapped_column(String(40), default="usable", nullable=False)
    defects_json: Mapped[str] = mapped_column(Text, nullable=False)
    suggestions_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    image: Mapped[GeneratedImage] = relationship(back_populates="reviews")


class Copywriting(Base):
    __tablename__ = "copywriting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    image_id: Mapped[Optional[int]] = mapped_column(ForeignKey("generated_images.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    selling_points_json: Mapped[str] = mapped_column(Text, nullable=False)
    xiaohongshu_title: Mapped[str] = mapped_column(String(220), nullable=False)
    xiaohongshu_text: Mapped[str] = mapped_column(Text, nullable=False)
    moments_text: Mapped[str] = mapped_column(Text, nullable=False)
    taobao_text: Mapped[str] = mapped_column(Text, nullable=False)
    douyin_script: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tags_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    project: Mapped[Project] = relationship(back_populates="copywriting_items")
    image: Mapped[Optional[GeneratedImage]] = relationship(back_populates="copywriting_items")


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    step_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    summary: Mapped[str] = mapped_column(String(300), nullable=False)
    detail_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    project: Mapped[Project] = relationship(back_populates="workflow_events")
