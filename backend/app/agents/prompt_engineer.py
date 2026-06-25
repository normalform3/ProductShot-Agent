import json

from app.agents.llm import generate_payload
from app.models import Project
from app.providers import TextProvider, get_text_provider
from app.schemas import CreativePlanPayload, ProductAnalysisPayload, PromptPackPayload


class PromptEngineerAgent:
    """Turns a selected creative plan into model-ready image prompts."""

    def __init__(self, text_provider: TextProvider | None = None) -> None:
        self.text_provider = text_provider or get_text_provider()

    def run(
        self,
        project: Project,
        plan: CreativePlanPayload,
        analysis: ProductAnalysisPayload | None = None,
    ) -> PromptPackPayload:
        size = self._size_for_platform(plan.applicable_platform or project.target_platform)
        model_payload = generate_payload(
            provider=self.text_provider,
            payload_type=PromptPackPayload,
            system_prompt=(
                "You are a prompt engineer for commercial product photography. "
                "Write model-ready image prompts in English, with Chinese consistency notes."
            ),
            user_prompt=json.dumps(
                {
                    "project": {
                        "product_name": project.product_name,
                        "product_category": project.product_category,
                        "target_platform": project.target_platform,
                        "core_selling_points": project.core_selling_points,
                    },
                    "plan": plan.model_dump(),
                    "product_consistency_rules": analysis.product_consistency_rules if analysis else [],
                    "size": size,
                    "required_fields": PromptPackPayload.model_json_schema(),
                },
                ensure_ascii=False,
            ),
            schema_name="PromptPackPayload",
            temperature=0.35,
        )
        if model_payload is not None:
            return model_payload

        consistency_rules = analysis.product_consistency_rules if analysis else []
        consistency_sentence = " ".join(consistency_rules) if consistency_rules else (
            "Keep the original product shape, color, label, logo, packaging structure, and material consistent."
        )
        positive = (
            f"Realistic product marketing photography for {project.product_name}. "
            f"Scene: {plan.visual_description}. Background: {plan.background_scene}. "
            f"Visual style: {plan.visual_style}. Highlight selling point: {plan.main_selling_point}. "
            f"{consistency_sentence} "
            "Professional commercial lighting, clean composition, high click appeal, platform-ready cover image."
        )
        negative = (
            "distorted product, changed label, duplicated product, messy background, unreadable text, fake watermark, "
            "extra fingers, low resolution, severe blur, overexposed highlights, random logo, AI artifacts"
        )
        return PromptPackPayload(
            positive_prompt=positive,
            negative_prompt=negative,
            size=size,
            style=plan.visual_style,
            product_consistency_notes="保持商品主体清晰，不改变商品形状、颜色、标签和关键材质；避免生成乱码文字。",
            platform=plan.applicable_platform or project.target_platform,
            generation_mode="image_to_image",
            reference_strength=0.72,
            consistency_rules=consistency_rules,
        )

    def _size_for_platform(self, platform: str) -> str:
        if "小红书" in platform:
            return "1024x1365"
        if "抖音" in platform:
            return "1080x1920"
        if "淘宝" in platform or "朋友圈" in platform:
            return "1024x1024"
        return "1024x1024"
