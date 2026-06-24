import json

from pydantic import BaseModel

from app.agents.llm import generate_payload
from app.models import Project
from app.providers import TextProvider, get_text_provider
from app.schemas import CreativePlanPayload, ProductAnalysisPayload


class CreativePlanListPayload(BaseModel):
    plans: list[CreativePlanPayload]


class CreativePlannerAgent:
    """Creates platform-aware marketing concepts from product analysis."""

    def __init__(self, text_provider: TextProvider | None = None) -> None:
        self.text_provider = text_provider or get_text_provider()

    def run(self, project: Project, analysis: ProductAnalysisPayload) -> list[CreativePlanPayload]:
        model_payload = generate_payload(
            provider=self.text_provider,
            payload_type=CreativePlanListPayload,
            system_prompt=(
                "You are a commercial visual planner. Create exactly three distinct product image concepts "
                "for ecommerce or social publishing. Keep ideas feasible for text-to-image generation."
            ),
            user_prompt=json.dumps(
                {
                    "project": {
                        "product_name": project.product_name,
                        "product_category": project.product_category,
                        "target_platform": project.target_platform,
                        "target_audience": project.target_audience,
                        "preferred_style": project.preferred_style,
                    },
                    "analysis": analysis.model_dump(),
                    "required_fields": CreativePlanListPayload.model_json_schema(),
                },
                ensure_ascii=False,
            ),
            schema_name="CreativePlanListPayload",
        )
        if model_payload is not None and model_payload.plans:
            return model_payload.plans[:3]

        primary_point = analysis.recommended_selling_points[0] if analysis.recommended_selling_points else "商品质感"
        platform = project.target_platform
        style = project.preferred_style or "清爽高级风"
        return [
            CreativePlanPayload(
                plan_name="高级极简白底风",
                applicable_platform=platform,
                visual_description=f"让「{project.product_name}」占据画面中心，使用干净白底和柔和阴影突出商品轮廓。",
                background_scene="浅色摄影棚背景、轻微投影、少量材质道具。",
                visual_style="高级、干净、可信赖",
                main_selling_point=primary_point,
                recommendation_reason="适合电商主图和首图，能快速建立商品专业感。",
                copywriting_direction="强调清晰卖点、品质感和购买理由。",
            ),
            CreativePlanPayload(
                plan_name="小红书生活方式风",
                applicable_platform="小红书",
                visual_description=f"把「{project.product_name}」放进真实生活场景，配合暖光和自然桌面陈列。",
                background_scene="居家桌面、杂志、杯子、织物或植物等轻量生活道具。",
                visual_style=style,
                main_selling_point=primary_point,
                recommendation_reason="更容易传达使用氛围，适合种草和收藏。",
                copywriting_direction="用第一人称体验感表达，避免硬广语气。",
            ),
            CreativePlanPayload(
                plan_name="节日礼物促销风",
                applicable_platform=platform,
                visual_description=f"围绕「{project.product_name}」构建礼物感陈列，加入礼盒、丝带和促销氛围。",
                background_scene="节日礼盒、丝带、暖色灯光、简洁促销角标区域。",
                visual_style="温暖、精致、有购买冲动",
                main_selling_point=analysis.recommended_selling_points[-1] if analysis.recommended_selling_points else "适合送礼",
                recommendation_reason="适合活动期、朋友圈转化和节日促销。",
                copywriting_direction="突出送礼理由、限时感和场景价值。",
            ),
        ]
