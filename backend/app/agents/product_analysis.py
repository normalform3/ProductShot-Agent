from __future__ import annotations

from app.models import Project
from app.schemas import ProductAnalysisPayload


class ProductAnalysisAgent:
    """Analyzes product metadata and image context for the marketing workflow."""

    def run(self, project: Project, image_path: str | None = None) -> ProductAnalysisPayload:
        category = project.product_category or "精选商品"
        audience = project.target_audience or "注重质感和效率的消费者"
        style = project.preferred_style or "清爽高级风"
        selling_points = self._split_points(project.core_selling_points)
        if not selling_points:
            selling_points = ["实用好搭配", "适合日常使用", "适合作为礼物"]

        issues = ["原图背景可能分散注意力", "需要进一步突出商品主体"]
        if image_path:
            issues.append("建议在生成图中保持原商品外观和标签一致")

        return ProductAnalysisPayload(
            product_type=f"{category}类商品",
            core_features=[
                f"商品名称为「{project.product_name}」",
                f"目标平台是{project.target_platform}",
                f"偏好的视觉方向是{style}",
            ],
            target_audience_analysis=f"{audience}更容易被清晰卖点、生活化场景和可信的使用理由打动。",
            recommended_selling_points=selling_points[:4],
            recommended_visual_styles=[style, "小红书生活方式风", "高级极简白底风"],
            image_issues=issues,
            marketing_angles=[
                "先用场景建立使用想象",
                "再用卖点降低购买决策成本",
                "最后用平台化文案提升点击和收藏意愿",
            ],
        )

    def _split_points(self, raw: str | None) -> list[str]:
        if not raw:
            return []
        normalized = raw.replace("，", ",").replace("、", ",").replace("\n", ",")
        return [item.strip() for item in normalized.split(",") if item.strip()]
