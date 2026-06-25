from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.agents import CreativePlannerAgent, ProductAnalysisAgent, RevisionAgent, VisualAnalysisAgent
from app.api.routes import test_text_model_connection as run_text_model_connection_test
from app.config import settings
from app.database import Base
from app.models import Copywriting, Project, WorkflowEvent
from app.providers import get_text_provider
from app.providers.dashscope_text_provider import DashscopeTextProvider
from app.providers.dashscope_image_provider import DashscopeImageProvider
from app.providers.mock_image_provider import MockImageProvider
from app.providers.text_provider import TextProviderUnavailable
from app.services import ProductShotWorkflow


def sample_project() -> Project:
    return Project(
        id=1,
        product_name="手工香薰蜡烛",
        product_category="家居香氛",
        core_selling_points="手工制作, 香味舒缓, 适合送礼",
        target_platform="小红书",
        target_audience="年轻女性",
        preferred_style="温暖治愈风",
    )


def test_product_analysis_agent_outputs_structured_marketing_context():
    project = sample_project()
    visual = VisualAnalysisAgent().run(project, "source.png")
    result = ProductAnalysisAgent().run(project, "source.png", visual)

    assert result.product_type == "家居香氛类商品"
    assert "手工制作" in result.recommended_selling_points
    assert result.image_issues
    assert result.product_consistency_rules


def test_creative_planner_agent_returns_three_plans():
    project = sample_project()
    analysis = ProductAnalysisAgent().run(project)
    plans = CreativePlannerAgent().run(project, analysis)

    assert len(plans) == 3
    assert {plan.plan_name for plan in plans} == {"电商质感主图", "社媒生活方式封面", "促销礼物海报"}
    assert all(plan.expected_outputs for plan in plans)


def test_revision_agent_classifies_copywriting_request():
    project = sample_project()
    analysis = ProductAnalysisAgent().run(project)
    plan = CreativePlannerAgent().run(project, analysis)[0]

    result = RevisionAgent().run(project, plan, "文案不要太夸张")

    assert result.revision_type == "copywriting"
    assert not result.should_regenerate


def test_mock_image_provider_copies_source_image(tmp_path: Path):
    source = tmp_path / "source.png"
    source.write_bytes(b"fake image bytes")
    provider = MockImageProvider()

    results = provider.generate_images(
        project_id=999,
        source_image_path=str(source),
        positive_prompt="prompt",
        negative_prompt="negative",
        size="1024x1024",
        count=2,
    )

    assert len(results) == 2
    assert all(item.image_path.exists() for item in results)


def test_text_provider_factory_uses_mock_by_default():
    original_provider = settings.text_provider
    try:
        settings.text_provider = "mock"
        provider = get_text_provider()
    finally:
        settings.text_provider = original_provider

    assert provider.name == "mock"


def test_dashscope_text_provider_requires_environment_key():
    original_key = settings.dashscope_api_key
    try:
        settings.dashscope_api_key = None
        provider = DashscopeTextProvider()
        try:
            provider.generate_json(system_prompt="x", user_prompt="y", schema_name="Test")
        except TextProviderUnavailable as exc:
            assert "DASHSCOPE_API_KEY" in str(exc)
        else:
            raise AssertionError("DashscopeTextProvider should require DASHSCOPE_API_KEY")
    finally:
        settings.dashscope_api_key = original_key


def test_dashscope_text_provider_uses_multimodal_sdk(monkeypatch):
    calls = {}
    dashscope_module = ModuleType("dashscope")
    dashscope_module.base_http_api_url = ""

    class FakeMultiModalConversation:
        @staticmethod
        def call(**kwargs):
            calls["kwargs"] = kwargs
            return SimpleNamespace(
                output=SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content=[{"text": '{"ok": true}'}])
                        )
                    ]
                )
            )

    dashscope_module.MultiModalConversation = FakeMultiModalConversation
    monkeypatch.setitem(sys.modules, "dashscope", dashscope_module)

    original_key = settings.dashscope_api_key
    original_base = settings.dashscope_base_http_api_url
    try:
        settings.dashscope_api_key = "test-key"
        settings.dashscope_base_http_api_url = "https://ws-k524juxb6rhpyhlp.cn-beijing.maas.aliyuncs.com/api/v1"
        provider = DashscopeTextProvider()
        result = provider.generate_json(system_prompt="system", user_prompt="user", schema_name="Test")
    finally:
        settings.dashscope_api_key = original_key
        settings.dashscope_base_http_api_url = original_base

    assert result == {"ok": True}
    assert dashscope_module.base_http_api_url == "https://ws-k524juxb6rhpyhlp.cn-beijing.maas.aliyuncs.com/api/v1"
    assert calls["kwargs"]["model"] == settings.text_model
    assert calls["kwargs"]["messages"][0]["content"][0]["text"]


def test_dashscope_image_provider_uses_image_generation_sdk(monkeypatch, tmp_path: Path):
    calls = {}
    dashscope_module = ModuleType("dashscope")
    dashscope_module.base_http_api_url = ""
    image_generation_module = ModuleType("dashscope.aigc.image_generation")
    response_module = ModuleType("dashscope.api_entities.dashscope_response")

    class FakeImageGeneration:
        @staticmethod
        def call(**kwargs):
            calls["kwargs"] = kwargs
            return SimpleNamespace(output=SimpleNamespace(results=[{"url": "https://example.com/generated.png"}]))

    class FakeMessage:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    image_generation_module.ImageGeneration = FakeImageGeneration
    response_module.Message = FakeMessage
    monkeypatch.setitem(sys.modules, "dashscope", dashscope_module)
    monkeypatch.setitem(sys.modules, "dashscope.aigc", ModuleType("dashscope.aigc"))
    monkeypatch.setitem(sys.modules, "dashscope.aigc.image_generation", image_generation_module)
    monkeypatch.setitem(sys.modules, "dashscope.api_entities", ModuleType("dashscope.api_entities"))
    monkeypatch.setitem(sys.modules, "dashscope.api_entities.dashscope_response", response_module)

    def fake_download(self, image_url, target):
        target.write_bytes(b"image")

    monkeypatch.setattr(DashscopeImageProvider, "_download_image", fake_download)
    source = tmp_path / "source.png"
    source.write_bytes(b"source")

    original_key = settings.dashscope_api_key
    try:
        settings.dashscope_api_key = "test-key"
        provider = DashscopeImageProvider()
        results = provider.generate_images(
            project_id=123,
            source_image_path=str(source),
            positive_prompt="prompt",
            negative_prompt="negative",
            size="1024x1024",
            count=1,
        )
    finally:
        settings.dashscope_api_key = original_key

    assert len(results) == 1
    assert calls["kwargs"]["model"] == "wan2.7-image-pro"
    assert calls["kwargs"]["size"] == "2K"
    assert calls["kwargs"]["messages"][0].kwargs["content"][0]["image"].startswith("file://")


def test_model_connection_test_returns_success_for_mock_provider():
    original_provider = settings.text_provider
    try:
        settings.text_provider = "mock"
        result = run_text_model_connection_test()
    finally:
        settings.text_provider = original_provider

    assert result.status == "success"
    assert result.provider == "mock"
    assert "Mock" in result.message


def test_model_connection_test_returns_failure_when_dashscope_key_missing():
    original_provider = settings.text_provider
    original_key = settings.dashscope_api_key
    try:
        settings.text_provider = "dashscope"
        settings.dashscope_api_key = None
        result = run_text_model_connection_test()
    finally:
        settings.text_provider = original_provider
        settings.dashscope_api_key = original_key

    assert result.status == "failed"
    assert result.provider == "dashscope"
    assert "DASHSCOPE_API_KEY" in result.message


def test_workflow_records_persistent_agent_event():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        project = sample_project()
        project.id = None
        project.status = "draft"
        db.add(project)
        db.commit()
        db.refresh(project)

        workflow = ProductShotWorkflow(db)
        workflow.analyze(project)

        events = db.query(WorkflowEvent).filter(WorkflowEvent.project_id == project.id).all()

    assert {event.step_key for event in events} == {"visual_analysis", "analysis"}
    assert all(event.status == "success" for event in events)
    assert all(event.latency_ms is not None for event in events)


def test_plan_stage_creates_three_directions_without_generation_tasks():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        project = sample_project()
        project.id = None
        project.status = "draft"
        db.add(project)
        db.commit()
        db.refresh(project)

        workflow = ProductShotWorkflow(db)
        plans = workflow.plan(project)

        task_count = len(project.generation_tasks)
        events = db.query(WorkflowEvent).filter(WorkflowEvent.project_id == project.id).all()

    assert len(plans) == 3
    assert task_count == 0
    assert {event.step_key for event in events} == {"visual_analysis", "analysis", "plans"}


def test_generate_pack_uses_selected_plan_and_creates_review_and_copy():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        project = sample_project()
        project.id = None
        project.status = "draft"
        db.add(project)
        db.commit()
        db.refresh(project)

        workflow = ProductShotWorkflow(db)
        workflow.plan(project)
        selected_plan = project.creative_plans[1]
        selected_plan_id = selected_plan.id
        result = workflow.generate_pack(project, selected_plan, 2)
        copy_count = db.query(Copywriting).filter(Copywriting.project_id == project.id).count()
        db.refresh(project)

    assert len(result.images) == 2
    assert all(image.plan_id == selected_plan_id for image in result.images)
    assert any(image.is_recommended for image in result.images)
    assert copy_count == 1
