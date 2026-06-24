from app.models import Project
from app.schemas import CreativePlanPayload, PromptPayload


class PromptEngineerAgent:
    """Turns a selected creative plan into model-ready image prompts."""

    def run(self, project: Project, plan: CreativePlanPayload) -> PromptPayload:
        size = self._size_for_platform(plan.applicable_platform or project.target_platform)
        positive = (
            f"Realistic product marketing photography for {project.product_name}. "
            f"Scene: {plan.visual_description}. Background: {plan.background_scene}. "
            f"Visual style: {plan.visual_style}. Highlight selling point: {plan.main_selling_point}. "
            "Keep the original product as the main subject, clear and sharp, with consistent shape, color, label, and material. "
            "Professional commercial lighting, clean composition, high click appeal, platform-ready cover image."
        )
        negative = (
            "distorted product, changed label, duplicated product, messy background, unreadable text, fake watermark, "
            "extra fingers, low resolution, severe blur, overexposed highlights, random logo, AI artifacts"
        )
        return PromptPayload(
            positive_prompt=positive,
            negative_prompt=negative,
            size=size,
            style=plan.visual_style,
            product_consistency_notes="保持商品主体清晰，不改变商品形状、颜色、标签和关键材质；避免生成乱码文字。",
        )

    def _size_for_platform(self, platform: str) -> str:
        if "小红书" in platform:
            return "1024x1365"
        if "抖音" in platform:
            return "1080x1920"
        if "淘宝" in platform or "朋友圈" in platform:
            return "1024x1024"
        return "1024x1024"

