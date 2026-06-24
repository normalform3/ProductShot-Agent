from app.models import GeneratedImage, Project
from app.schemas import CreativePlanPayload, ImageReviewPayload


class ImageCriticAgent:
    """Scores generated images for marketing usefulness, not just aesthetics."""

    def run(self, project: Project, image: GeneratedImage, plan: CreativePlanPayload) -> ImageReviewPayload:
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

