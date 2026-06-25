from datetime import UTC, datetime
from time import perf_counter

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.database import get_db
from app.models import CreativePlan, GeneratedImage, GenerationTask, ProductAsset, Project, WorkflowEvent
from app.providers import get_text_provider
from app.providers.text_provider import TextProviderError, TextProviderUnavailable
from app.schemas import (
    CopywritingRead,
    CopywritingRequest,
    CreativePlanRead,
    GenerateImagesRequest,
    GeneratedImageRead,
    GeneratedImagesResponse,
    ImageReviewRead,
    ModelConnectionTestRead,
    ModelSettingsRead,
    ModelSettingsUpdate,
    ProductAnalysisRead,
    ProductAssetRead,
    ProjectCreate,
    ProjectDetail,
    ProjectRead,
    RevisionRequest,
    RevisionResponse,
    WorkflowEventRead,
)
from app.services import ProductShotWorkflow
from app.storage import save_upload_file

router = APIRouter(prefix="/api")

TEXT_PROVIDERS = {"mock", "dashscope"}
IMAGE_PROVIDERS = {"mock", "dashscope", "openai"}


def get_project_or_404(db: Session, project_id: int) -> Project:
    project = (
        db.query(Project)
        .options(
            selectinload(Project.assets),
            selectinload(Project.analyses),
            selectinload(Project.creative_plans),
            selectinload(Project.generation_tasks),
            selectinload(Project.generated_images).selectinload(GeneratedImage.reviews),
            selectinload(Project.generated_images).selectinload(GeneratedImage.task).selectinload(GenerationTask.plan),
            selectinload(Project.copywriting_items),
            selectinload(Project.workflow_events),
        )
        .filter(Project.id == project_id)
        .first()
    )
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.get("/model-settings", response_model=ModelSettingsRead)
def get_model_settings() -> ModelSettingsRead:
    return _model_settings_read()


@router.put("/model-settings", response_model=ModelSettingsRead)
def update_model_settings(payload: ModelSettingsUpdate) -> ModelSettingsRead:
    updates = payload.model_dump(exclude_unset=True)
    if "text_provider" in updates:
        value = updates["text_provider"].lower()
        if value not in TEXT_PROVIDERS:
            raise HTTPException(status_code=400, detail="不支持的文字模型 Provider")
        settings.text_provider = value
    if "image_provider" in updates:
        value = updates["image_provider"].lower()
        if value not in IMAGE_PROVIDERS:
            raise HTTPException(status_code=400, detail="不支持的图片模型 Provider")
        settings.image_provider = value
    if "text_model" in updates and updates["text_model"]:
        settings.text_model = updates["text_model"]
    if "image_model" in updates and updates["image_model"]:
        settings.dashscope_image_model = updates["image_model"]
    if "dashscope_text_base_url" in updates and updates["dashscope_text_base_url"]:
        settings.dashscope_base_http_api_url = updates["dashscope_text_base_url"].rstrip("/")
        settings.dashscope_text_base_url = settings.dashscope_base_http_api_url
        settings.dashscope_image_generation_url = settings.dashscope_base_http_api_url
    if "dashscope_image_generation_url" in updates and updates["dashscope_image_generation_url"]:
        settings.dashscope_base_http_api_url = updates["dashscope_image_generation_url"].rstrip("/")
        settings.dashscope_text_base_url = settings.dashscope_base_http_api_url
        settings.dashscope_image_generation_url = settings.dashscope_base_http_api_url
    return _model_settings_read()


@router.post("/model-settings/test-text", response_model=ModelConnectionTestRead)
def test_text_model_connection() -> ModelConnectionTestRead:
    provider = get_text_provider()
    started = perf_counter()
    checked_at = datetime.now(UTC).replace(tzinfo=None)
    model = getattr(provider, "model", settings.text_model)
    if provider.name == "mock":
        return ModelConnectionTestRead(
            provider=provider.name,
            model=model,
            status="success",
            latency_ms=0,
            message="Mock Provider 不需要外部 LLM 连接。",
            checked_at=checked_at,
        )

    try:
        result = provider.generate_json(
            system_prompt="You are a connection test endpoint. Return a minimal JSON object.",
            user_prompt='Return {"ok": true, "message": "connected"} as JSON.',
            schema_name="ConnectionTest",
            temperature=0,
        )
        ok = bool(result.get("ok", True))
        status = "success" if ok else "failed"
        message = str(result.get("message") or ("LLM 连接测试通过。" if ok else "LLM 返回了非成功结果。"))
    except (TextProviderUnavailable, TextProviderError) as exc:
        status = "failed"
        message = str(exc)
    except Exception as exc:
        status = "failed"
        message = f"LLM connection test failed: {exc}"

    return ModelConnectionTestRead(
        provider=provider.name,
        model=model,
        status=status,
        latency_ms=max(0, int((perf_counter() - started) * 1000)),
        message=message,
        checked_at=checked_at,
    )


def _model_settings_read() -> ModelSettingsRead:
    return ModelSettingsRead(
        text_provider=settings.text_provider,
        text_model=settings.text_model,
        image_provider=settings.image_provider,
        image_model=settings.dashscope_image_model,
        dashscope_text_base_url=settings.dashscope_base_http_api_url,
        dashscope_image_generation_url=settings.dashscope_base_http_api_url,
        dashscope_workspace_id_configured=bool(settings.dashscope_workspace_id),
        dashscope_api_key_configured=bool(settings.dashscope_api_key),
        available_text_providers=sorted(TEXT_PROVIDERS),
        available_image_providers=sorted(IMAGE_PROVIDERS),
    )


@router.post("/projects", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    project = Project(**payload.model_dump(), status="draft")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return db.query(Project).order_by(Project.updated_at.desc()).all()


@router.get("/projects/{project_id}", response_model=ProjectDetail)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectDetail:
    project = get_project_or_404(db, project_id)
    workflow = ProductShotWorkflow(db)
    latest_visual = workflow.latest_visual_analysis(project_id)
    latest_analysis = workflow.latest_analysis(project_id)
    latest_copy = project.copywriting_items[-1] if project.copywriting_items else None
    workflow_events = (
        db.query(WorkflowEvent)
        .filter(WorkflowEvent.project_id == project_id)
        .order_by(WorkflowEvent.started_at.desc(), WorkflowEvent.id.desc())
        .limit(80)
        .all()
    )
    return ProjectDetail(
        **ProjectRead.model_validate(project).model_dump(),
        assets=[ProductAssetRead.model_validate(item) for item in project.assets],
        visual_analysis=workflow.visual_analysis_read(latest_visual) if latest_visual else None,
        product_strategy=workflow.analysis_read(latest_analysis) if latest_analysis else None,
        latest_analysis=workflow.analysis_read(latest_analysis) if latest_analysis else None,
        creative_plans=[workflow.creative_plan_read(item) for item in project.creative_plans],
        generated_images=[GeneratedImageRead.model_validate(item) for item in project.generated_images],
        latest_copywriting=workflow.copywriting_read(latest_copy) if latest_copy else None,
        workflow_events=[WorkflowEventRead.model_validate(item) for item in workflow_events],
    )


@router.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    project = get_project_or_404(db, project_id)
    db.delete(project)
    db.commit()
    return {"message": "项目已删除"}


@router.post("/projects/{project_id}/assets", response_model=ProductAssetRead)
def upload_asset(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)) -> ProductAsset:
    project = get_project_or_404(db, project_id)
    try:
        file_path, file_url, file_type = save_upload_file(project_id, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    has_asset = db.query(ProductAsset).filter(ProductAsset.project_id == project_id).first() is not None
    asset = ProductAsset(
        project_id=project_id,
        file_url=file_url,
        file_path=file_path,
        file_type=file_type,
        is_primary=not has_asset,
    )
    project.status = "draft"
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/projects/{project_id}/assets", response_model=list[ProductAssetRead])
def list_assets(project_id: int, db: Session = Depends(get_db)) -> list[ProductAsset]:
    get_project_or_404(db, project_id)
    return db.query(ProductAsset).filter(ProductAsset.project_id == project_id).order_by(ProductAsset.created_at.desc()).all()


@router.post("/projects/{project_id}/agent/analyze", response_model=ProductAnalysisRead)
def analyze_project(project_id: int, db: Session = Depends(get_db)) -> ProductAnalysisRead:
    project = get_project_or_404(db, project_id)
    return ProductShotWorkflow(db).analyze(project)


@router.post("/projects/{project_id}/agent/generate-plans", response_model=list[CreativePlanRead])
def generate_plans(project_id: int, db: Session = Depends(get_db)) -> list[CreativePlanRead]:
    project = get_project_or_404(db, project_id)
    return ProductShotWorkflow(db).generate_plans(project)


@router.post("/projects/{project_id}/agent/plan", response_model=list[CreativePlanRead])
def plan_project(project_id: int, db: Session = Depends(get_db)) -> list[CreativePlanRead]:
    project = get_project_or_404(db, project_id)
    return ProductShotWorkflow(db).plan(project)


@router.get("/projects/{project_id}/creative-plans", response_model=list[CreativePlanRead])
def list_plans(project_id: int, db: Session = Depends(get_db)) -> list[CreativePlanRead]:
    get_project_or_404(db, project_id)
    workflow = ProductShotWorkflow(db)
    rows = db.query(CreativePlan).filter(CreativePlan.project_id == project_id).order_by(CreativePlan.created_at.asc()).all()
    return [workflow.creative_plan_read(row) for row in rows]


@router.post("/projects/{project_id}/creative-plans/{plan_id}/generate-images", response_model=GeneratedImagesResponse)
def generate_images(
    project_id: int,
    plan_id: int,
    payload: GenerateImagesRequest,
    db: Session = Depends(get_db),
) -> GeneratedImagesResponse:
    project = get_project_or_404(db, project_id)
    plan = db.query(CreativePlan).filter(CreativePlan.id == plan_id, CreativePlan.project_id == project_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="创意方案不存在")
    try:
        return ProductShotWorkflow(db).generate_images(project, plan, payload.count)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"图片生成失败：{exc}") from exc


@router.post("/projects/{project_id}/creative-plans/{plan_id}/generate-pack", response_model=GeneratedImagesResponse)
def generate_pack(
    project_id: int,
    plan_id: int,
    payload: GenerateImagesRequest,
    db: Session = Depends(get_db),
) -> GeneratedImagesResponse:
    project = get_project_or_404(db, project_id)
    plan = db.query(CreativePlan).filter(CreativePlan.id == plan_id, CreativePlan.project_id == project_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="创意方案不存在")
    try:
        return ProductShotWorkflow(db).generate_pack(project, plan, payload.count)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"素材包生成失败：{exc}") from exc


@router.get("/projects/{project_id}/generated-images", response_model=list[GeneratedImageRead])
def list_generated_images(project_id: int, db: Session = Depends(get_db)) -> list[GeneratedImage]:
    get_project_or_404(db, project_id)
    return db.query(GeneratedImage).filter(GeneratedImage.project_id == project_id).order_by(GeneratedImage.created_at.desc()).all()


@router.post("/projects/{project_id}/generated-images/{image_id}/review", response_model=ImageReviewRead)
def review_image(project_id: int, image_id: int, db: Session = Depends(get_db)) -> ImageReviewRead:
    project = get_project_or_404(db, project_id)
    image = (
        db.query(GeneratedImage)
        .options(selectinload(GeneratedImage.task).selectinload(GenerationTask.plan))
        .filter(GeneratedImage.id == image_id, GeneratedImage.project_id == project_id)
        .first()
    )
    if image is None:
        raise HTTPException(status_code=404, detail="生成图片不存在")
    try:
        return ProductShotWorkflow(db).review_image(project, image)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/projects/{project_id}/copywriting", response_model=CopywritingRead)
def create_copywriting(project_id: int, payload: CopywritingRequest, db: Session = Depends(get_db)) -> CopywritingRead:
    project = get_project_or_404(db, project_id)
    image = None
    if payload.image_id:
        image = (
            db.query(GeneratedImage)
            .options(
                selectinload(GeneratedImage.task).selectinload(GenerationTask.plan),
                selectinload(GeneratedImage.reviews),
            )
            .filter(GeneratedImage.id == payload.image_id, GeneratedImage.project_id == project_id)
            .first()
        )
        if image is None:
            raise HTTPException(status_code=404, detail="生成图片不存在")
    try:
        return ProductShotWorkflow(db).create_copywriting(project, image)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/projects/{project_id}/revise", response_model=RevisionResponse)
def revise_project(project_id: int, payload: RevisionRequest, db: Session = Depends(get_db)) -> RevisionResponse:
    project = get_project_or_404(db, project_id)
    try:
        return ProductShotWorkflow(db).revise(project, payload.instruction)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/projects/{project_id}/export/json")
def export_json(project_id: int, db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)
    project.status = "exported"
    db.commit()
    report = ProductShotWorkflow(db).export_report(project)
    return report


@router.get("/projects/{project_id}/export/markdown")
def export_markdown(project_id: int, db: Session = Depends(get_db)) -> Response:
    project = get_project_or_404(db, project_id)
    project.status = "exported"
    db.commit()
    report = ProductShotWorkflow(db).export_report(project)
    markdown = _report_to_markdown(report)
    return Response(content=markdown, media_type="text/markdown; charset=utf-8")


def _report_to_markdown(report) -> str:
    lines = [
        f"# {report.project.product_name} 营销素材报告",
        "",
        f"- 目标平台：{report.project.target_platform}",
        f"- 商品类别：{report.project.product_category or '未填写'}",
        f"- 目标人群：{report.project.target_audience or '未填写'}",
        f"- 风格偏好：{report.project.preferred_style or '未填写'}",
        "",
        "## 商品分析",
    ]
    if report.analysis:
        lines += [
            f"- 商品类型：{report.analysis.product_type}",
            f"- 目标人群分析：{report.analysis.target_audience_analysis}",
            f"- 推荐卖点：{'、'.join(report.analysis.recommended_selling_points)}",
            f"- 图片问题：{'、'.join(report.analysis.image_issues)}",
        ]
    lines += ["", "## 创意方案"]
    for plan in report.creative_plans:
        lines += [
            f"### {plan.plan_name}",
            f"- 画面：{plan.plan.visual_description}",
            f"- 主打卖点：{plan.plan.main_selling_point}",
            f"- 推荐理由：{plan.plan.recommendation_reason}",
        ]
    lines += ["", "## 生成图片与评分"]
    for image in report.generated_images:
        lines += [f"- 图片：{image.image_url}，评分：{image.score or '待评分'}"]
    lines += ["", "## 文案"]
    for copy in report.copywriting:
        lines += [
            f"### {copy.copywriting.title}",
            f"- 小红书标题：{copy.copywriting.xiaohongshu_title}",
            f"- 小红书正文：{copy.copywriting.xiaohongshu_text}",
            f"- 朋友圈文案：{copy.copywriting.moments_text}",
            f"- 淘宝短文案：{copy.copywriting.taobao_text}",
            f"- 标签：{'、'.join(copy.copywriting.tags)}",
        ]
    return "\n".join(lines) + "\n"
