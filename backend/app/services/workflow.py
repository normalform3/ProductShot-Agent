from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents import (
    CopywritingAgent,
    CreativePlannerAgent,
    ImageCriticAgent,
    ProductAnalysisAgent,
    PromptEngineerAgent,
    RevisionAgent,
)
from app.models import (
    Copywriting,
    CreativePlan,
    GeneratedImage,
    GenerationTask,
    ImageReview,
    ProductAnalysis,
    ProductAsset,
    Project,
)
from app.providers import get_image_provider
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
    ProjectRead,
    RevisionResponse,
)
from app.utils.json import dumps, loads


class ProductShotWorkflow:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.analysis_agent = ProductAnalysisAgent()
        self.planner_agent = CreativePlannerAgent()
        self.prompt_agent = PromptEngineerAgent()
        self.critic_agent = ImageCriticAgent()
        self.copywriting_agent = CopywritingAgent()
        self.revision_agent = RevisionAgent()

    def analyze(self, project: Project) -> ProductAnalysisRead:
        primary = self.primary_asset(project.id)
        payload = self.analysis_agent.run(project, primary.file_path if primary else None)
        row = ProductAnalysis(project_id=project.id, analysis_json=payload.model_dump_json())
        project.status = "analyzed"
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self.analysis_read(row)

    def generate_plans(self, project: Project) -> list[CreativePlanRead]:
        analysis = self.latest_analysis(project.id)
        if analysis is None:
            analysis = self.analyze(project)
            analysis_payload = analysis.analysis
        else:
            analysis_payload = ProductAnalysisPayload.model_validate_json(analysis.analysis_json)

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
        return [self.creative_plan_read(row) for row in rows]

    def generate_images(self, project: Project, plan: CreativePlan, count: int) -> GeneratedImagesResponse:
        payload = CreativePlanPayload.model_validate_json(plan.plan_json)
        prompt = self.prompt_agent.run(project, payload)
        task = GenerationTask(
            project_id=project.id,
            plan_id=plan.id,
            prompt=prompt.positive_prompt,
            negative_prompt=prompt.negative_prompt,
            model_name=get_image_provider().name,
            status="running",
        )
        self.db.add(task)
        self.db.flush()
        primary = self.primary_asset(project.id)
        provider = get_image_provider()
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
            return GeneratedImagesResponse(
                task=GenerationTaskRead.model_validate(task),
                prompt=prompt,
                images=[GeneratedImageRead.model_validate(image) for image in images],
            )
        except Exception as exc:
            task.status = "failed"
            task.error_message = str(exc)
            self.db.commit()
            raise

    def review_image(self, project: Project, image: GeneratedImage) -> ImageReviewRead:
        if image.task.plan is None:
            raise ValueError("生成图片缺少创意方案")
        plan_payload = CreativePlanPayload.model_validate_json(image.task.plan.plan_json)
        payload = self.critic_agent.run(project, image, plan_payload)
        row = ImageReview(
            image_id=image.id,
            overall_score=payload.overall_score,
            product_clarity_score=payload.product_clarity,
            style_match_score=payload.style_match,
            commercial_value_score=payload.commercial_value,
            platform_fit_score=payload.platform_fit,
            defects_json=dumps(payload.defects),
            suggestions_json=dumps(payload.suggestions),
        )
        image.score = payload.overall_score
        project.status = "reviewed"
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self.review_read(row)

    def create_copywriting(self, project: Project, image: GeneratedImage | None) -> CopywritingRead:
        plan = image.task.plan if image and image.task else self.latest_plan(project.id)
        if plan is None:
            raise ValueError("请先生成创意方案")
        plan_payload = CreativePlanPayload.model_validate_json(plan.plan_json)
        latest_review = image.reviews[-1] if image and image.reviews else None
        review_payload = self.review_payload(latest_review) if latest_review else None
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
            tags_json=dumps(payload.tags),
        )
        project.status = "copywritten"
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self.copywriting_read(row)

    def revise(self, project: Project, instruction: str) -> RevisionResponse:
        plan = self.latest_plan(project.id)
        if plan is None:
            raise ValueError("请先生成创意方案")
        payload = CreativePlanPayload.model_validate_json(plan.plan_json)
        response = self.revision_agent.run(project, payload, instruction)
        project.status = "revised"
        self.db.commit()
        return response

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
            style_match=row.style_match_score,
            commercial_value=row.commercial_value_score,
            platform_fit=row.platform_fit_score,
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
            tags=loads(row.tags_json, []),
        )
        return CopywritingRead(
            id=row.id,
            project_id=row.project_id,
            image_id=row.image_id,
            copywriting=payload,
            created_at=row.created_at,
        )
