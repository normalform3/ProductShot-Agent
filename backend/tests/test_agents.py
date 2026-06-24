from pathlib import Path

from app.agents import CreativePlannerAgent, ProductAnalysisAgent, RevisionAgent
from app.models import Project
from app.providers.mock_image_provider import MockImageProvider


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

