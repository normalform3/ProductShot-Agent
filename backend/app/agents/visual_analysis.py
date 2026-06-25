from __future__ import annotations

import json

from app.agents.llm import generate_payload
from app.models import Project
from app.providers import TextProvider, get_text_provider
from app.providers.text_provider import TextProviderUnavailable
from app.schemas import VisualAnalysisPayload


class VisualAnalysisAgent:
    """Extracts product fidelity and marketing cues from the uploaded source image."""

    def __init__(self, text_provider: TextProvider | None = None) -> None:
        self.text_provider = text_provider or get_text_provider()

    def run(self, project: Project, image_path: str | None = None) -> VisualAnalysisPayload:
        if image_path and hasattr(self.text_provider, "generate_multimodal_json"):
            try:
                data = self.text_provider.generate_multimodal_json(  # type: ignore[attr-defined]
                    system_prompt=(
                        "You are a commercial product-photo analyst. Inspect the source product image and "
                        "return structured Chinese JSON for downstream image generation and marketing planning."
                    ),
                    user_prompt=json.dumps(
                        {
                            "product_name": project.product_name,
                            "product_category": project.product_category,
                            "target_platform": project.target_platform,
                            "required_fields": VisualAnalysisPayload.model_json_schema(),
                        },
                        ensure_ascii=False,
                    ),
                    image_path=image_path,
                    schema_name="VisualAnalysisPayload",
                    temperature=0.2,
                )
                return VisualAnalysisPayload.model_validate(data)
            except TextProviderUnavailable:
                pass

        return self._fallback(project, has_image=bool(image_path))

    def _fallback(self, project: Project, *, has_image: bool) -> VisualAnalysisPayload:
        category = project.product_category or "商品"
        style = project.preferred_style or "干净商业摄影"
        appearance = f"围绕「{project.product_name}」的{category}主体，优先保持真实外观、比例和包装信息。"
        background_issues = ["原图背景可能分散注意力", "需要增强主体光线和边缘清晰度"] if has_image else ["尚未上传可分析原图"]
        return VisualAnalysisPayload(
            product_appearance=appearance,
            dominant_colors=["参考原图主色", "自然中性色"],
            materials=["参考原图材质", "保持商品真实质感"],
            visible_text_or_logo=["保留原图可见品牌、标签和包装文字"],
            subject_clarity="需要让商品主体在生成图中保持清晰、完整、无遮挡。",
            background_issues=background_issues,
            fidelity_constraints=[
                "不改变商品形状、颜色、标签、Logo 和包装结构",
                "不生成额外商品主体，不遮挡关键卖点区域",
                "避免乱码文字、水印和伪造认证标识",
            ],
            marketing_opportunities=[
                f"用{style}强化第一眼质感",
                f"围绕{project.target_platform}首图需求突出主体",
                "用更干净的场景降低购买决策成本",
            ],
        )
