from __future__ import annotations

import json

from app.agents.llm import generate_payload
from app.models import Project
from app.providers import TextProvider, get_text_provider
from app.schemas import CopywritingPayload, CreativePlanPayload, ImageReviewPayload


class CopywritingAgent:
    """Generates platform-ready copy that matches the selected concept and review."""

    def __init__(self, text_provider: TextProvider | None = None) -> None:
        self.text_provider = text_provider or get_text_provider()

    def run(
        self,
        project: Project,
        plan: CreativePlanPayload,
        review: ImageReviewPayload | None = None,
    ) -> CopywritingPayload:
        model_payload = generate_payload(
            provider=self.text_provider,
            payload_type=CopywritingPayload,
            system_prompt=(
                "You are a Chinese ecommerce copywriter. Write concise, platform-ready copy "
                "that avoids exaggerated or unverifiable claims."
            ),
            user_prompt=json.dumps(
                {
                    "project": {
                        "product_name": project.product_name,
                        "product_category": project.product_category,
                        "core_selling_points": project.core_selling_points,
                        "target_platform": project.target_platform,
                        "target_audience": project.target_audience,
                    },
                    "plan": plan.model_dump(),
                    "review": review.model_dump() if review else None,
                    "required_fields": CopywritingPayload.model_json_schema(),
                },
                ensure_ascii=False,
            ),
            schema_name="CopywritingPayload",
            temperature=0.6,
        )
        if model_payload is not None:
            return model_payload

        selling_points = self._split_points(project.core_selling_points) or [
            plan.main_selling_point,
            "日常使用场景丰富",
            "拍照和送礼都很合适",
        ]
        score_phrase = "画面完成度很高" if review and review.overall_score >= 88 else "画面重点更清楚"
        title = f"{project.product_name}｜{plan.main_selling_point}"
        xhs_title = f"发现一个让生活更有质感的{project.product_category or '好物'}"
        tags = ["商品图", project.target_platform, plan.visual_style, "小商家营销", "种草文案"]
        return CopywritingPayload(
            title=title,
            selling_points=selling_points[:4],
            xiaohongshu_title=xhs_title,
            xiaohongshu_text=(
                f"最近在整理店里的{project.product_name}，这组图走的是「{plan.visual_style}」。"
                f"它最打动人的点是{plan.main_selling_point}，放在{plan.background_scene}里会更有真实使用感。"
                f"{score_phrase}，适合做{project.target_platform}首图或种草封面。"
            ),
            moments_text=(
                f"{project.product_name}上新啦。{plan.main_selling_point}，整体风格干净耐看，"
                f"适合{project.target_audience or '日常自用和送礼'}。感兴趣可以私信我。"
            ),
            taobao_text=(
                f"{project.product_name}，主打{plan.main_selling_point}。画面采用{plan.visual_style}，"
                "突出商品主体和使用场景，适合作为商品主图、详情页首屏和活动素材。"
            ),
            tags=tags,
        )

    def _split_points(self, raw: str | None) -> list[str]:
        if not raw:
            return []
        normalized = raw.replace("，", ",").replace("、", ",").replace("\n", ",")
        return [item.strip() for item in normalized.split(",") if item.strip()]
