from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agents import (
    CopywritingAgent,
    CreativePlannerAgent,
    ImageCriticAgent,
    ProductAnalysisAgent,
    PromptEngineerAgent,
    RevisionAgent,
    VisualAnalysisAgent,
)
from app.models import (
    Copywriting,
    CreativePlan,
    GeneratedImage,
    GenerationTask,
    ImageReview,
    ProductAnalysis,
    ProductAsset,
    ProductVisualAnalysis,
    Project,
    WorkflowEvent,
)
from app.providers import get_image_provider, get_text_provider
from app.schemas import (
    CopywritingPayload,
    CopywritingRead,
    CreativePlanPayload,
    CreativePlanRead,
    ExportReport,
    GeneratedImageRead,
    GeneratedImagesResponse,
    GenerationTaskRead,
    ImageReviewPayload,
    ImageReviewRead,
    ProductAnalysisPayload,
    ProductAnalysisRead,
    ProductAssetRead,
    ProductVisualAnalysisRead,
    ProjectRead,
    RevisionResponse,
    VisualAnalysisPayload,
    WorkflowEventRead,
)
from app.utils.json import dumps, loads


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class ProductShotWorkflow:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.text_provider = get_text_provider()
        self.visual_agent = VisualAnalysisAgent(self.text_provider)
        self.analysis_agent = ProductAnalysisAgent(self.text_provider)
        self.planner_agent = CreativePlannerAgent(self.text_provider)
        self.prompt_agent = PromptEngineerAgent(self.text_provider)
        self.critic_agent = ImageCriticAgent(self.text_provider)
        self.copywriting_agent = CopywritingAgent(self.text_provider)
        self.revision_agent = RevisionAgent(self.text_provider)

    def plan(self, project: Project) -> list[CreativePlanRead]:
        self.ensure_visual_analysis(project)
        self.analyze(project)
        return self.generate_plans(project)

    def ensure_visual_analysis(self, project: Project) -> ProductVisualAnalysisRead:
        existing = self.latest_visual_analysis(project.id)
        if existing is not None:
            return self.visual_analysis_read(existing)

        started_at = utcnow()
        primary = self.primary_asset(project.id)
        try:
            payload = self.visual_agent.run(project, primary.file_path if primary else None)
            row = ProductVisualAnalysis(project_id=project.id, analysis_json=payload.model_dump_json())
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
            self.record_event(
                project.id,
                step_key="visual_analysis",
                agent_name="VisualAnalysisAgent",
                status="success",
                summary="完成原图视觉理解和商品保真约束提取。",
                detail=payload.model_dump(),
                started_at=started_at,
            )
            return self.visual_analysis_read(row)
        except Exception as exc:
            self.record_event(
                project.id,
                step_key="visual_analysis",
                agent_name="VisualAnalysisAgent",
                status="failed",
                summary="原图视觉理解失败。",
                detail={"has_primary_asset": bool(primary)},
                error_message=str(exc),
                started_at=started_at,
            )
            raise

    def analyze(self, project: Project) -> ProductAnalysisRead:
        started_at = utcnow()
        primary = self.primary_asset(project.id)
        visual_read = self.ensure_visual_analysis(project)
        try:
            payload = self.analysis_agent.run(project, primary.file_path if primary else None, visual_read.analysis)
            row = ProductAnalysis(project_id=project.id, analysis_json=payload.model_dump_json())
            project.status = "analyzed"
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
            self.record_event(
                project.id,
                step_key="analysis",
                agent_name="ProductAnalysisAgent",
                status="success",
                summary=f"识别为 {payload.product_type}，提炼 {len(payload.recommended_selling_points)} 个推荐卖点。",
                detail={
                    "product_type": payload.product_type,
                    "recommended_selling_points": payload.recommended_selling_points,
                    "image_issues": payload.image_issues,
                },
                started_at=started_at,
            )
            return self.analysis_read(row)
        except Exception as exc:
            self.record_event(
                project.id,
                step_key="analysis",
                agent_name="ProductAnalysisAgent",
                status="failed",
                summary="商品分析失败。",
                detail={"has_primary_asset": bool(primary)},
                error_message=str(exc),
                started_at=started_at,
            )
            raise

    def generate_plans(self, project: Project) -> list[CreativePlanRead]:
        started_at = utcnow()
        analysis = self.latest_analysis(project.id)
        if analysis is None:
            analysis = self.analyze(project)
            analysis_payload = analysis.analysis
        else:
            analysis_payload = ProductAnalysisPayload.model_validate_json(analysis.analysis_json)

        try:
            for old in self.db.query(CreativePlan).filter(CreativePlan.project_id == project.id).all():
                self.db.delete(old)
            self.db.flush()

            payloads = self.planner_agent.run(project, analysis_payload)
            rows: list[CreativePlan] = []
            for payload in payloads:
                row = CreativePlan(
                    project_id=project.id,
                    plan_name=payload.plan_name,
                    plan_description=payload.visual_description,
                    target_platform=payload.applicable_platform,
                    visual_style=payload.visual_style,
                    selling_angle=payload.main_selling_point,
                    plan_json=payload.model_dump_json(),
                )
                self.db.add(row)
                rows.append(row)
            project.status = "planned"
            self.db.commit()
            self.record_event(
                project.id,
                step_key="plans",
                agent_name="CreativePlannerAgent",
                status="success",
                summary=f"生成 {len(payloads)} 个创意方向。",
                detail={"plans": [payload.plan_name for payload in payloads]},
                started_at=started_at,
            )
            return [self.creative_plan_read(row) for row in rows]
        except Exception as exc:
            self.record_event(
                project.id,
                step_key="plans",
                agent_name="CreativePlannerAgent",
                status="failed",
                summary="创意方案生成失败。",
                detail={"analysis_product_type": analysis_payload.product_type},
                error_message=str(exc),
                started_at=started_at,
            )
            raise

    def generate_images(self, project: Project, plan: CreativePlan, count: int) -> GeneratedImagesResponse:
        payload = CreativePlanPayload.model_validate_json(plan.plan_json)
        analysis_row = self.latest_analysis(project.id)
        analysis_payload = ProductAnalysisPayload.model_validate_json(analysis_row.analysis_json) if analysis_row else None
        prompt_started_at = utcnow()
        try:
            prompt = self.prompt_agent.run(project, payload, analysis_payload)
            self.record_event(
                project.id,
                step_key="prompt",
                agent_name="PromptEngineerAgent",
                status="success",
                summary=f"构建 {prompt.size} 的图片生成 Prompt。",
                detail={
                    "plan_name": payload.plan_name,
                    "size": prompt.size,
                    "style": prompt.style,
                    "positive_prompt": prompt.positive_prompt,
                    "negative_prompt": prompt.negative_prompt,
                    "generation_mode": prompt.generation_mode,
                    "reference_strength": prompt.reference_strength,
                },
                started_at=prompt_started_at,
            )
        except Exception as exc:
            self.record_event(
                project.id,
                step_key="prompt",
                agent_name="PromptEngineerAgent",
                status="failed",
                summary="Prompt 构建失败。",
                detail={"plan_name": payload.plan_name},
                error_message=str(exc),
                started_at=prompt_started_at,
            )
            raise

        provider = get_image_provider()
        provider_model = getattr(provider, "model", provider.name)
        primary = self.primary_asset(project.id)
        capabilities = getattr(provider, "capabilities", {"text_to_image"})
        if prompt.generation_mode in {"image_to_image", "reference_image"} and primary and "image_to_image" not in capabilities:
            raise RuntimeError(f"{provider.name} ImageProvider does not support source-image generation.")
        task = GenerationTask(
            project_id=project.id,
            plan_id=plan.id,
            prompt=prompt.positive_prompt,
            negative_prompt=prompt.negative_prompt,
            model_name=provider_model,
            status="running",
        )
        self.db.add(task)
        self.db.flush()
        prompt_pack_id = f"prompt_{task.id}_{uuid4().hex[:8]}"
        image_started_at = utcnow()
        try:
            generated = provider.generate_images(
                project_id=project.id,
                source_image_path=primary.file_path if primary else None,
                positive_prompt=prompt.positive_prompt,
                negative_prompt=prompt.negative_prompt,
                size=prompt.size,
                count=count,
            )
            images = [
                GeneratedImage(
                    task_id=task.id,
                    project_id=project.id,
                    plan_id=plan.id,
                    platform=prompt.platform,
                    generation_mode=prompt.generation_mode,
                    prompt_pack_id=prompt_pack_id,
                    prompt_pack_json=prompt.model_dump_json(),
                    image_url=item.image_url,
                    image_path=str(item.image_path),
                    width=item.width,
                    height=item.height,
                    is_selected=index == 0,
                )
                for index, item in enumerate(generated)
            ]
            self.db.add_all(images)
            task.status = "success"
            project.status = "generated"
            self.db.commit()
            self.record_event(
                project.id,
                step_key="images",
                agent_name=f"{provider.name} ImageProvider",
                status="success",
                summary=f"生成 {len(images)} 张营销图片。",
                detail={
                    "task_id": task.id,
                    "plan_id": plan.id,
                    "model_name": provider_model,
                    "count": len(images),
                    "prompt": task.prompt,
                    "negative_prompt": task.negative_prompt,
                    "generation_mode": prompt.generation_mode,
                    "image_ids": [image.id for image in images],
                },
                started_at=image_started_at,
            )
            return GeneratedImagesResponse(
                task=GenerationTaskRead.model_validate(task),
                prompt=prompt,
                images=[GeneratedImageRead.model_validate(image) for image in images],
            )
        except Exception as exc:
            task.status = "failed"
            task.error_message = str(exc)
            self.db.commit()
            self.record_event(
                project.id,
                step_key="images",
                agent_name=f"{provider.name} ImageProvider",
                status="failed",
                summary="图片生成失败。",
                detail={"task_id": task.id, "plan_id": plan.id, "model_name": provider_model},
                error_message=str(exc),
                started_at=image_started_at,
            )
            raise

    def generate_pack(self, project: Project, plan: CreativePlan, count: int) -> GeneratedImagesResponse:
        result = self.generate_images(project, plan, count)
        images = (
            self.db.query(GeneratedImage)
            .filter(GeneratedImage.task_id == result.task.id)
            .order_by(GeneratedImage.id.asc())
            .all()
        )
        for image in images:
            self.review_image(project, image)

        refreshed = (
            self.db.query(GeneratedImage)
            .filter(GeneratedImage.task_id == result.task.id)
            .order_by(GeneratedImage.score.desc().nullslast(), GeneratedImage.id.asc())
            .all()
        )
        best = refreshed[0] if refreshed else None
        if best is not None:
            for image in refreshed:
                image.is_recommended = image.id == best.id
                image.is_selected = image.id == best.id
            self.db.commit()
            self.create_copywriting(project, best)

        final_images = (
            self.db.query(GeneratedImage)
            .filter(GeneratedImage.task_id == result.task.id)
            .order_by(GeneratedImage.is_recommended.desc(), GeneratedImage.id.asc())
            .all()
        )
        return GeneratedImagesResponse(
            task=result.task,
            prompt=result.prompt,
            images=[GeneratedImageRead.model_validate(image) for image in final_images],
        )

    def review_image(self, project: Project, image: GeneratedImage) -> ImageReviewRead:
        started_at = utcnow()
        if image.task.plan is None:
            raise ValueError("生成图片缺少创意方案")
        plan_payload = CreativePlanPayload.model_validate_json(image.task.plan.plan_json)
        visual = self.visual_analysis_payload(self.latest_visual_analysis(project.id))
        primary = self.primary_asset(project.id)
        try:
            payload = self.critic_agent.run(project, image, plan_payload, visual, primary.file_path if primary else None)
            row = ImageReview(
                image_id=image.id,
                overall_score=payload.overall_score,
                product_clarity_score=payload.product_clarity,
                product_consistency_score=payload.product_consistency,
                style_match_score=payload.style_match,
                commercial_value_score=payload.commercial_value,
                platform_fit_score=payload.platform_fit,
                text_artifact_risk=payload.text_artifact_risk,
                ai_artifact_risk=payload.ai_artifact_risk,
                recommendation_level=payload.recommendation_level,
                defects_json=dumps(payload.defects),
                suggestions_json=dumps(payload.suggestions),
            )
            image.score = payload.overall_score
            project.status = "reviewed"
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
            self.record_event(
                project.id,
                step_key="review",
                agent_name="ImageCriticAgent",
                status="success",
                summary=f"图片 {image.id} 评分 {payload.overall_score}。",
                detail=payload.model_dump(),
                started_at=started_at,
            )
            return self.review_read(row)
        except Exception as exc:
            self.record_event(
                project.id,
                step_key="review",
                agent_name="ImageCriticAgent",
                status="failed",
                summary=f"图片 {image.id} 评价失败。",
                detail={"image_id": image.id},
                error_message=str(exc),
                started_at=started_at,
            )
            raise

    def create_copywriting(self, project: Project, image: GeneratedImage | None) -> CopywritingRead:
        started_at = utcnow()
        plan = image.task.plan if image and image.task else self.latest_plan(project.id)
        if plan is None:
            raise ValueError("请先生成创意方案")
        plan_payload = CreativePlanPayload.model_validate_json(plan.plan_json)
        latest_review = image.reviews[-1] if image and image.reviews else None
        review_payload = self.review_payload(latest_review) if latest_review else None
        try:
            payload = self.copywriting_agent.run(project, plan_payload, review_payload)
            row = Copywriting(
                project_id=project.id,
                image_id=image.id if image else None,
                title=payload.title,
                selling_points_json=dumps(payload.selling_points),
                xiaohongshu_title=payload.xiaohongshu_title,
                xiaohongshu_text=payload.xiaohongshu_text,
                moments_text=payload.moments_text,
                taobao_text=payload.taobao_text,
                douyin_script=payload.douyin_script,
                tags_json=dumps(payload.tags),
            )
            project.status = "copywritten"
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
            self.record_event(
                project.id,
                step_key="copy",
                agent_name="CopywritingAgent",
                status="success",
                summary=f"生成标题和 {len(payload.tags)} 个标签。",
                detail={"title": payload.title, "tags": payload.tags, "image_id": image.id if image else None},
                started_at=started_at,
            )
            return self.copywriting_read(row)
        except Exception as exc:
            self.record_event(
                project.id,
                step_key="copy",
                agent_name="CopywritingAgent",
                status="failed",
                summary="文案生成失败。",
                detail={"image_id": image.id if image else None},
                error_message=str(exc),
                started_at=started_at,
            )
            raise

    def revise(self, project: Project, instruction: str) -> RevisionResponse:
        started_at = utcnow()
        plan = self.latest_plan(project.id)
        if plan is None:
            raise ValueError("请先生成创意方案")
        payload = CreativePlanPayload.model_validate_json(plan.plan_json)
        try:
            response = self.revision_agent.run(project, payload, instruction)
            project.status = "revised"
            self.db.commit()
            self.record_event(
                project.id,
                step_key="revision",
                agent_name="RevisionAgent",
                status="success",
                summary=f"识别为 {response.revision_type} 修改，目标：{response.target}。",
                detail={
                    "instruction": instruction,
                    "revision_type": response.revision_type,
                    "target": response.target,
                    "should_regenerate": response.should_regenerate,
                    "modification_plan": response.modification_plan,
                },
                started_at=started_at,
            )
            return response
        except Exception as exc:
            self.record_event(
                project.id,
                step_key="revision",
                agent_name="RevisionAgent",
                status="failed",
                summary="修改意图分析失败。",
                detail={"instruction": instruction},
                error_message=str(exc),
                started_at=started_at,
            )
            raise

    def export_report(self, project: Project, revision: RevisionResponse | None = None) -> ExportReport:
        return ExportReport(
            project=ProjectRead.model_validate(project),
            assets=[ProductAssetRead.model_validate(item) for item in project.assets],
            analysis=self.analysis_payload(self.latest_analysis(project.id)),
            creative_plans=[self.creative_plan_read(item) for item in project.creative_plans],
            generation_tasks=[GenerationTaskRead.model_validate(item) for item in project.generation_tasks],
            generated_images=[GeneratedImageRead.model_validate(item) for item in project.generated_images],
            image_reviews=[
                self.review_read(review)
                for image in project.generated_images
                for review in image.reviews
            ],
            copywriting=[self.copywriting_read(item) for item in project.copywriting_items],
            revision=revision,
            metadata={"provider": get_image_provider().name, "status": project.status},
        )

    def workflow_event_read(self, row: WorkflowEvent) -> WorkflowEventRead:
        return WorkflowEventRead.model_validate(row)

    def record_event(
        self,
        project_id: int,
        *,
        step_key: str,
        agent_name: str,
        status: str,
        summary: str,
        detail: dict | None = None,
        error_message: str | None = None,
        started_at: datetime | None = None,
    ) -> WorkflowEvent:
        started = started_at or utcnow()
        ended = utcnow()
        row = WorkflowEvent(
            project_id=project_id,
            step_key=step_key,
            agent_name=agent_name,
            status=status,
            summary=summary[:300],
            detail_json=dumps(detail or {}),
            error_message=error_message,
            started_at=started,
            ended_at=ended,
            latency_ms=max(0, int((ended - started).total_seconds() * 1000)),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def primary_asset(self, project_id: int) -> ProductAsset | None:
        return (
            self.db.query(ProductAsset)
            .filter(ProductAsset.project_id == project_id)
            .order_by(ProductAsset.is_primary.desc(), ProductAsset.id.asc())
            .first()
        )

    def latest_analysis(self, project_id: int) -> ProductAnalysis | None:
        return (
            self.db.query(ProductAnalysis)
            .filter(ProductAnalysis.project_id == project_id)
            .order_by(ProductAnalysis.created_at.desc())
            .first()
        )

    def latest_visual_analysis(self, project_id: int) -> ProductVisualAnalysis | None:
        return (
            self.db.query(ProductVisualAnalysis)
            .filter(ProductVisualAnalysis.project_id == project_id)
            .order_by(ProductVisualAnalysis.created_at.desc())
            .first()
        )

    def latest_plan(self, project_id: int) -> CreativePlan | None:
        return (
            self.db.query(CreativePlan)
            .filter(CreativePlan.project_id == project_id)
            .order_by(CreativePlan.created_at.desc())
            .first()
        )

    def analysis_payload(self, row: ProductAnalysis | None) -> ProductAnalysisPayload | None:
        if row is None:
            return None
        return ProductAnalysisPayload.model_validate_json(row.analysis_json)

    def visual_analysis_payload(self, row: ProductVisualAnalysis | None) -> VisualAnalysisPayload | None:
        if row is None:
            return None
        return VisualAnalysisPayload.model_validate_json(row.analysis_json)

    def visual_analysis_read(self, row: ProductVisualAnalysis) -> ProductVisualAnalysisRead:
        return ProductVisualAnalysisRead(
            id=row.id,
            project_id=row.project_id,
            analysis=VisualAnalysisPayload.model_validate_json(row.analysis_json),
            created_at=row.created_at,
        )

    def analysis_read(self, row: ProductAnalysis) -> ProductAnalysisRead:
        return ProductAnalysisRead(
            id=row.id,
            project_id=row.project_id,
            analysis=ProductAnalysisPayload.model_validate_json(row.analysis_json),
            created_at=row.created_at,
        )

    def creative_plan_read(self, row: CreativePlan) -> CreativePlanRead:
        return CreativePlanRead(
            id=row.id,
            project_id=row.project_id,
            plan_name=row.plan_name,
            plan_description=row.plan_description,
            target_platform=row.target_platform,
            visual_style=row.visual_style,
            selling_angle=row.selling_angle,
            plan=CreativePlanPayload.model_validate_json(row.plan_json),
            created_at=row.created_at,
        )

    def review_payload(self, row: ImageReview) -> ImageReviewPayload:
        return ImageReviewPayload(
            overall_score=row.overall_score,
            product_clarity=row.product_clarity_score,
            product_consistency=row.product_consistency_score,
            style_match=row.style_match_score,
            commercial_value=row.commercial_value_score,
            platform_fit=row.platform_fit_score,
            text_artifact_risk=row.text_artifact_risk,
            ai_artifact_risk=row.ai_artifact_risk,
            recommendation_level=row.recommendation_level,
            defects=loads(row.defects_json, []),
            suggestions=loads(row.suggestions_json, []),
        )

    def review_read(self, row: ImageReview) -> ImageReviewRead:
        return ImageReviewRead(id=row.id, image_id=row.image_id, review=self.review_payload(row), created_at=row.created_at)

    def copywriting_read(self, row: Copywriting) -> CopywritingRead:
        payload = CopywritingPayload(
            title=row.title,
            selling_points=loads(row.selling_points_json, []),
            xiaohongshu_title=row.xiaohongshu_title,
            xiaohongshu_text=row.xiaohongshu_text,
            moments_text=row.moments_text,
            taobao_text=row.taobao_text,
            douyin_script=getattr(row, "douyin_script", "") or "",
            tags=loads(row.tags_json, []),
        )
        return CopywritingRead(
            id=row.id,
            project_id=row.project_id,
            image_id=row.image_id,
            copywriting=payload,
            created_at=row.created_at,
        )
