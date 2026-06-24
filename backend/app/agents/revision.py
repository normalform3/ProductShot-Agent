import json

from app.agents.llm import generate_payload
from app.agents.prompt_engineer import PromptEngineerAgent
from app.models import Project
from app.providers import TextProvider, get_text_provider
from app.schemas import CreativePlanPayload, PromptPayload, RevisionResponse


class RevisionAgent:
    """Classifies natural-language revision intent and creates the next action plan."""

    def __init__(self, text_provider: TextProvider | None = None) -> None:
        self.text_provider = text_provider or get_text_provider()
        self.prompt_agent = PromptEngineerAgent(self.text_provider)

    def run(self, project: Project, plan: CreativePlanPayload, instruction: str) -> RevisionResponse:
        base_prompt = self.prompt_agent.run(project, plan)
        model_payload = generate_payload(
            provider=self.text_provider,
            payload_type=RevisionResponse,
            system_prompt=(
                "You are an agent workflow controller. Classify the user's revision request and decide "
                "whether image regeneration is needed. Return a practical modification plan."
            ),
            user_prompt=json.dumps(
                {
                    "project": {
                        "product_name": project.product_name,
                        "target_platform": project.target_platform,
                    },
                    "plan": plan.model_dump(),
                    "current_prompt": base_prompt.model_dump(),
                    "instruction": instruction,
                    "allowed_revision_types": ["copywriting", "platform", "prompt", "style", "creative_plan", "image"],
                    "required_fields": RevisionResponse.model_json_schema(),
                },
                ensure_ascii=False,
            ),
            schema_name="RevisionResponse",
            temperature=0.25,
        )
        if model_payload is not None:
            return model_payload

        revision_type = self._classify(instruction)
        new_prompt = PromptPayload(
            positive_prompt=f"{base_prompt.positive_prompt} Revision request: {instruction}.",
            negative_prompt=base_prompt.negative_prompt,
            size=base_prompt.size,
            style=plan.visual_style,
            product_consistency_notes=base_prompt.product_consistency_notes,
        )
        should_regenerate = revision_type in {"image", "style", "platform", "prompt", "creative_plan"}
        return RevisionResponse(
            revision_type=revision_type,
            target=self._target_label(revision_type),
            modification_plan=self._plan_for(revision_type, instruction),
            new_prompt=new_prompt,
            should_regenerate=should_regenerate,
            notes="MVP 阶段返回修改计划和新 Prompt；真实图片编辑模型接入后可在此触发局部重绘或重生成。",
        )

    def _classify(self, instruction: str) -> str:
        text = instruction.lower()
        if any(word in text for word in ["文案", "标题", "语气", "夸张"]):
            return "copywriting"
        if any(word in text for word in ["小红书", "淘宝", "朋友圈", "抖音", "平台"]):
            return "platform"
        if any(word in text for word in ["prompt", "提示词"]):
            return "prompt"
        if any(word in text for word in ["风格", "高级", "日系", "圣诞", "节日"]):
            return "style"
        if any(word in text for word in ["方案", "创意", "方向"]):
            return "creative_plan"
        return "image"

    def _target_label(self, revision_type: str) -> str:
        labels = {
            "copywriting": "营销文案",
            "platform": "平台适配",
            "prompt": "图片 Prompt",
            "style": "视觉风格",
            "creative_plan": "创意方案",
            "image": "生成图片",
        }
        return labels[revision_type]

    def _plan_for(self, revision_type: str, instruction: str) -> list[str]:
        common = [f"解析用户修改要求：{instruction}", "保留商品主体一致性和核心卖点"]
        mapping = {
            "copywriting": ["调整标题和正文语气", "重新生成平台文案"],
            "platform": ["切换平台尺寸和构图重点", "重新检查平台适配度"],
            "prompt": ["重写正向 Prompt", "补充反向约束"],
            "style": ["强化目标风格关键词", "调整场景、光线和道具"],
            "creative_plan": ["重新规划画面方向", "更新卖点表达方式"],
            "image": ["调整主体比例和背景元素", "建议重新生成图片版本"],
        }
        return common + mapping[revision_type]
