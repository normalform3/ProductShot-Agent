from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.agents import CreativePlannerAgent, ProductAnalysisAgent, RevisionAgent
from app.api.routes import test_text_model_connection as run_text_model_connection_test
from app.config import settings
from app.database import Base
from app.models import Project, WorkflowEvent
from app.providers import get_text_provider
from app.providers.dashscope_text_provider import DashscopeTextProvider
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
    result = ProductAnalysisAgent().run(project)

    assert result.product_type == "家居香氛类商品"
    assert "手工制作" in result.recommended_selling_points
    assert result.image_issues


def test_creative_planner_agent_returns_three_plans():
    project = sample_project()
    analysis = ProductAnalysisAgent().run(project)
    plans = CreativePlannerAgent().run(project, analysis)

    assert len(plans) == 3
    assert {plan.plan_name for plan in plans} == {"高级极简白底风", "小红书生活方式风", "节日礼物促销风"}


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

    assert len(events) == 1
    assert events[0].step_key == "analysis"
    assert events[0].status == "success"
    assert events[0].latency_ms is not None
