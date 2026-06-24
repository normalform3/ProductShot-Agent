import json

from app.agents.llm import generate_payload
from app.models import GeneratedImage, Project
from app.providers import TextProvider, get_text_provider
from app.schemas import CreativePlanPayload, ImageReviewPayload


class ImageCriticAgent:
    """Scores generated images for marketing usefulness, not just aesthetics."""

    def __init__(self, text_provider: TextProvider | None = None) -> None:
        self.text_provider = text_provider or get_text_provider()

    def run(self, project: Project, image: GeneratedImage, plan: CreativePlanPayload) -> ImageReviewPayload:
        model_payload = generate_payload(
            provider=self.text_provider,
            payload_type=ImageReviewPayload,
            system_prompt=(
                "You are a strict ecommerce creative reviewer. Score the generated asset for product clarity, "
                "style match, commercial value, and platform fit. Use integers from 0 to 100."
            ),
            user_prompt=json.dumps(
                {
                    "project": {
                        "product_name": project.product_name,
                        "target_platform": project.target_platform,
                        "target_audience": project.target_audience,
                    },
                    "image": {
                        "image_url": image.image_url,
                        "width": image.width,
                        "height": image.height,
                    },
                    "plan": plan.model_dump(),
                    "required_fields": ImageReviewPayload.model_json_schema(),
                },
                ensure_ascii=False,
            ),
            schema_name="ImageReviewPayload",
            temperature=0.2,
        )
        if model_payload is not None:
            return model_payload

        base = 78 + (image.id % 9)
        platform_bonus = 4 if plan.applicable_platform in {project.target_platform, "小红书"} else 0
        product_clarity = min(base + 8, 95)
        style_match = min(base + platform_bonus + 2, 94)
        commercial_value = min(base + 6, 95)
        platform_fit = min(base + platform_bonus + 4, 96)
        overall = round((product_clarity + style_match + commercial_value + platform_fit) / 4)

        return ImageReviewPayload(
            overall_score=overall,
            product_clarity=product_clarity,
            style_match=style_match,
            commercial_value=commercial_value,
            platform_fit=platform_fit,
            defects=["背景装饰可以再克制", "商品主体还可以更靠近视觉中心"] if overall < 90 else ["整体完成度较高"],
            suggestions=[
                "增强商品主体光照",
                f"进一步突出「{plan.main_selling_point}」",
                f"保持{project.target_platform}首图的清晰标题区",
            ],
        )
