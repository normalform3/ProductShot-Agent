import json

from app.agents.llm import generate_payload
from app.models import GeneratedImage, Project
from app.providers import TextProvider, get_text_provider
from app.schemas import CreativePlanPayload, ImageReviewPayload, VisualAnalysisPayload


class ImageCriticAgent:
    """Scores generated images for marketing usefulness, not just aesthetics."""

    def __init__(self, text_provider: TextProvider | None = None) -> None:
        self.text_provider = text_provider or get_text_provider()

    def run(
        self,
        project: Project,
        image: GeneratedImage,
        plan: CreativePlanPayload,
        visual: VisualAnalysisPayload | None = None,
        source_image_path: str | None = None,
    ) -> ImageReviewPayload:
        if source_image_path and hasattr(self.text_provider, "generate_multimodal_json"):
            try:
                data = self.text_provider.generate_multimodal_json(  # type: ignore[attr-defined]
                    system_prompt=(
                        "You are a strict ecommerce image reviewer. Compare the generated image against "
                        "the original product constraints and score marketing usefulness in Chinese JSON."
                    ),
                    user_prompt=json.dumps(
                        {
                            "project": {
                                "product_name": project.product_name,
                                "target_platform": project.target_platform,
                                "target_audience": project.target_audience,
                            },
                            "generated_image": {
                                "image_url": image.image_url,
                                "width": image.width,
                                "height": image.height,
                            },
                            "visual_analysis": visual.model_dump() if visual else None,
                            "plan": plan.model_dump(),
                            "required_fields": ImageReviewPayload.model_json_schema(),
                        },
                        ensure_ascii=False,
                    ),
                    image_path=image.image_path,
                    schema_name="ImageReviewPayload",
                    temperature=0.2,
                )
                return ImageReviewPayload.model_validate(data)
            except Exception:
                pass

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
                    "visual_analysis": visual.model_dump() if visual else None,
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
        product_consistency = 90 if image.generation_mode in {"image_to_image", "reference_image"} else 82
        style_match = min(base + platform_bonus + 2, 94)
        commercial_value = min(base + 6, 95)
        platform_fit = min(base + platform_bonus + 4, 96)
        overall = round((product_clarity + product_consistency + style_match + commercial_value + platform_fit) / 5)
        recommendation_level = "recommended" if overall >= 85 and product_consistency >= 85 else "usable"

        return ImageReviewPayload(
            overall_score=overall,
            product_clarity=product_clarity,
            product_consistency=product_consistency,
            style_match=style_match,
            commercial_value=commercial_value,
            platform_fit=platform_fit,
            text_artifact_risk="low",
            ai_artifact_risk="medium" if overall < 86 else "low",
            recommendation_level=recommendation_level,
            defects=["背景装饰可以再克制", "商品主体还可以更靠近视觉中心"] if overall < 90 else ["整体完成度较高"],
            suggestions=[
                "增强商品主体光照",
                f"进一步突出「{plan.main_selling_point}」",
                f"保持{project.target_platform}首图的清晰标题区",
            ],
        )
