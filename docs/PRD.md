# ProductShot Agent 产品需求文档

来源：`/Users/nate/Downloads/ProductShot Agent PRD.pdf`

## 1. 产品定位

ProductShot Agent 是一个面向淘宝、闲鱼、小红书、抖音小店、朋友圈卖货等轻量商家的 AI 商品营销内容生成平台。

用户上传一张或多张普通商品图，并填写少量商品信息后，系统自动生成多种风格的商品营销图、社媒封面图、促销图、商品卖点文案和发布文案，帮助小商家低成本完成商品内容包装。

本项目不是单点图片生成器，而是围绕“商品营销内容生产”的多 Agent 工作流系统。

## 2. 目标用户

核心用户：

- 淘宝、拼多多、闲鱼小卖家。
- 小红书、抖音、朋友圈卖货用户。
- 手作、饰品、美妆、食品、服装、数码配件等小商品经营者。
- 没有设计能力、没有专业摄影设备的小商家。
- 需要快速批量生成商品内容的个体创业者。

用户特点：

- 不擅长设计、构图和营销文案。
- 不想学习复杂提示词。
- 需要低成本、高效率生成内容。
- 更关心“能不能卖货”，而不只是图片艺术性。
- 需要适配小红书封面、朋友圈图、商品详情页图等多平台场景。

## 3. 用户痛点

图片层面：

- 原始商品图背景杂乱。
- 商品质感无法体现。
- 缺少生活化使用场景。
- 商品图不适合做社媒封面。
- 无法快速生成节日促销图、活动图、海报图。

文案层面：

- 不知道如何提炼商品卖点。
- 不会写小红书种草文案。
- 不会写朋友圈销售文案。
- 标题没有点击吸引力。
- 文案和图片风格不统一。

工作流层面：

- 不知道选择什么风格。
- 不知道如何写生图提示词。
- 不知道如何评价图片好坏。
- 修改时只能凭感觉反复试错。
- 很难一次性生成完整营销素材包。

## 4. 产品目标

核心目标：让小商家可以通过一次商品上传，快速获得一套可用于发布的商品营销素材。

MVP 目标：

- 用户上传商品图。
- 用户填写商品名称、卖点、目标平台、目标人群。
- 系统自动分析商品。
- 系统生成多种营销创意方案。
- 用户选择创意方案。
- 系统生成商品营销图。
- 系统生成标题、卖点文案、社媒文案。
- 系统对生成图片进行评分和建议。
- 用户可以基于自然语言继续修改。
- 用户可以导出图片和文案。

## 5. 核心功能

### 5.1 商品图上传

支持上传一张或多张商品图片。

支持格式：

- JPG
- PNG
- WebP

上传后系统需要完成：

- 图片存储。
- 图片预览。
- 商品主体识别。
- 背景复杂度判断。
- 图片清晰度检测。
- 商品类型初步识别。

### 5.2 商品信息填写

用户填写：

- 商品名称。
- 商品类别。
- 核心卖点。
- 目标人群。
- 目标平台。
- 想要的风格。
- 是否需要促销信息。
- 是否需要品牌名。
- 是否需要价格信息。

商品类别、目标人群、风格可以支持 AI 自动推荐。

### 5.3 商品分析 Agent

职责：理解用户上传的商品和填写的信息。

输入：

- 商品图片。
- 商品名称。
- 用户填写的卖点。
- 商品类别。
- 目标平台。

输出：

- 商品类型。
- 商品核心特征。
- 潜在目标人群。
- 可突出的卖点。
- 适合的视觉风格。
- 适合的营销角度。
- 可能存在的图片问题。

示例输出：

```json
{
  "product_type": "手工香薰蜡烛",
  "target_audience": ["年轻女性", "租房独居人群", "礼物购买者"],
  "selling_points": ["手工制作", "香味舒缓", "适合作为礼物", "提升房间氛围"],
  "recommended_styles": ["温暖治愈风", "高级礼物风", "生活方式风"],
  "image_issues": ["原图背景杂乱", "光线不足", "商品质感不明显"]
}
```

### 5.4 创意策划 Agent

职责：根据商品分析结果生成多个营销创意方向。

每个创意方案包括：

- 方案名称。
- 适用平台。
- 画面描述。
- 背景场景。
- 视觉风格。
- 主打卖点。
- 推荐文案方向。
- 适用人群。
- 预期营销效果。

### 5.5 Prompt 生成 Agent

职责：把创意方案转换为图片生成模型可用的提示词。

需要处理：

- 主体描述。
- 场景描述。
- 光线描述。
- 构图描述。
- 风格描述。
- 商品保真要求。
- 禁止项。
- 平台尺寸要求。

关键约束：提示词必须强调保持原商品外观、形状、标签和主体一致，避免变形、重复商品、错误文字和过度装饰。

### 5.6 图片生成工具

图片生成工具是 Agent 调用的外部工具，不是 Agent。

可选模型：

- OpenAI 图片生成模型。
- Stable Diffusion。
- ComfyUI 工作流。
- 阿里通义万相。
- 即梦、火山、腾讯混元等国内模型。

需要支持：

- 文生图。
- 图生图。
- 局部重绘。
- 背景替换。
- 多尺寸生成。
- 批量生成。
- 生成任务状态查询。

### 5.7 图片评价 Agent

职责：判断生成图片是否适合营销使用，而不只是判断图片是否好看。

评价维度：

- 商品主体是否清晰。
- 商品是否变形。
- 商品是否被遮挡。
- 背景是否干净。
- 风格是否符合用户需求。
- 是否突出核心卖点。
- 是否适合目标平台。
- 是否有点击吸引力。
- 是否存在文字错误。
- 是否存在明显 AI 瑕疵。

评分结构：

```json
{
  "overall_score": 86,
  "product_clarity": 90,
  "style_match": 85,
  "commercial_value": 88,
  "platform_fit": 84,
  "defects": ["背景略复杂", "商品边缘有轻微变形"],
  "suggestions": ["建议增强商品主体光照", "减少背景装饰物", "突出礼物属性"]
}
```

### 5.8 文案生成 Agent

职责：根据商品信息和生成图片输出配套文案。

支持内容：

- 商品标题。
- 商品卖点。
- 小红书标题。
- 小红书正文。
- 朋友圈文案。
- 淘宝详情页短文案。
- 抖音口播文案。
- 标签推荐。

### 5.9 修改迭代 Agent

用户可以用自然语言继续修改生成结果，例如：

- 背景更高级一点。
- 商品再大一点。
- 去掉旁边的咖啡杯。
- 改成圣诞节风格。
- 更适合小红书封面。
- 文案不要太夸张。
- 风格更像日系杂志。

修改迭代 Agent 需要判断用户想修改的是图片、文案、风格、尺寸、平台、创意方案还是商品卖点，然后调用对应工具执行修改。

### 5.10 多平台导出

支持平台和尺寸：

- 小红书封面：3:4。
- 抖音封面：9:16。
- 朋友圈图：1:1。
- 淘宝主图：1:1。
- 淘宝详情图：750px 宽。
- 海报图：9:16。
- 横版宣传图：16:9。

导出内容：

- 图片文件。
- 标题。
- 正文文案。
- 标签。
- 商品卖点。
- 发布建议。

## 6. Agent 使用边界

应该使用 Agent 的地方：

- 商品理解。
- 用户意图识别。
- 创意方案生成。
- 生图 Prompt 生成。
- 文案生成。
- 图片质量评价。
- 修改意图理解。
- 多轮迭代决策。
- 品牌风格总结。
- 平台发布建议。

不应该使用 Agent 的地方：

- 用户登录注册。
- 图片上传。
- 文件存储。
- 数据库增删改查。
- 图片格式转换。
- 图片尺寸裁剪。
- 任务队列。
- 生成进度查询。
- 支付系统。
- 权限控制。
- 历史记录管理。
- 模板渲染。
- 导出 ZIP 文件。
- 接口参数校验。
- 平台尺寸规则匹配。

工程原则：规则明确、结果稳定的逻辑用普通代码实现；需要模糊理解、创意生成、语义判断和多轮决策的环节才交给 Agent。

## 7. 核心用户流程

### 7.1 首次生成流程

1. 用户进入首页。
2. 点击“创建商品营销图”。
3. 上传商品图片。
4. 填写商品名称、卖点、目标平台。
5. 点击“开始分析”。
6. 商品分析 Agent 输出商品分析结果。
7. 创意策划 Agent 生成 3 到 5 个创意方案。
8. 用户选择一个方案。
9. Prompt Agent 生成图片提示词。
10. 图片生成工具生成 4 张图片。
11. 评价 Agent 对图片打分。
12. 系统推荐最佳图片。
13. 文案 Agent 生成配套标题和文案。
14. 用户选择满意版本。
15. 导出图片和文案。

### 7.2 修改流程

1. 用户选择一张生成图。
2. 输入修改要求。
3. 修改迭代 Agent 判断修改类型。
4. 系统调用图片编辑工具或文案生成工具。
5. 生成新版本。
6. 评价 Agent 重新评分。
7. 用户继续修改或导出。

## 8. 功能模块

### 8.1 项目管理模块

功能：

- 创建项目。
- 查看项目列表。
- 查看项目详情。
- 删除项目。
- 复制项目。
- 保存生成历史。

项目字段：

- 项目 ID。
- 用户 ID。
- 商品名称。
- 商品类别。
- 目标平台。
- 项目状态。
- 创建时间。
- 更新时间。

### 8.2 商品素材模块

- 上传商品图。
- 查看原图。
- 查看处理后的图片。
- 删除图片。
- 设置主图。
- 图片质量检测。

### 8.3 创意方案模块

- 生成创意方案。
- 查看方案详情。
- 收藏方案。
- 重新生成方案。
- 基于方案生成图片。

### 8.4 图片生成模块

- 根据方案生成图片。
- 批量生成多张图片。
- 查看生成进度。
- 查看失败原因。
- 重新生成。
- 局部修改。
- 背景替换。

### 8.5 图片评价模块

- 自动评分。
- 展示评分维度。
- 展示问题说明。
- 给出优化建议。
- 自动推荐最佳图片。

### 8.6 文案生成模块

- 生成商品标题。
- 生成商品卖点。
- 生成小红书文案。
- 生成朋友圈文案。
- 生成淘宝详情短文案。
- 生成标签。
- 改写文案语气。

### 8.7 导出模块

- 单图下载。
- 多图打包下载。
- 文案复制。
- 导出 Markdown。
- 导出 ZIP。
- 按平台导出不同尺寸。

## 9. 页面设计

首页：

- 产品介绍。
- 上传入口。
- 示例案例。
- 使用流程。
- 开始创建按钮。
- 主标题：上传一张商品图，生成一整套营销素材。
- 副标题：自动生成商品场景图、社媒封面、卖点文案和发布内容，适合小商家快速做内容。

创建项目页：

- 商品图片上传区域。
- 商品名称输入框。
- 商品类别选择。
- 核心卖点输入框。
- 目标平台选择。
- 目标人群选择。
- 风格偏好选择。
- 开始生成按钮。

Agent 工作流页：

- 正在分析商品。
- 正在生成创意方案。
- 正在生成图片 Prompt。
- 正在调用图片生成模型。
- 正在评价图片质量。
- 正在生成营销文案。
- 正在整理导出素材。

创意方案选择页：

- 展示多个方案卡片。
- 每个卡片包括方案名称、方案描述、适合平台、主打卖点、推荐理由、生成按钮。

生成结果页：

- 原始商品图。
- 生成图片列表。
- 每张图片评分。
- 推荐标签。
- 问题说明。
- 修改输入框。
- 文案结果。
- 导出按钮。

历史项目页：

- 项目名称。
- 商品缩略图。
- 生成数量。
- 更新时间。
- 项目状态。
- 继续编辑按钮。

## 10. 技术架构建议

前端推荐：

- Vue 3。
- TypeScript。
- Vite。
- Element Plus 或 Naive UI。
- Pinia。
- Axios。
- Tailwind CSS。

前端重点：

- 上传交互。
- Agent 流程可视化。
- 图片网格展示。
- 多版本对比。
- 评分展示。
- 自然语言修改框。
- 导出体验。

后端推荐：

- FastAPI 或 Spring Boot。
- MySQL。
- Redis。
- Celery / RQ / BullMQ / RabbitMQ。
- MinIO / OSS。
- WebSocket / SSE。
- LangGraph。

后端重点：

- 用户项目管理。
- 图片上传和存储。
- Agent 工作流编排。
- 异步任务队列。
- 生成任务状态管理。
- 图片结果存储。
- 导出文件生成。

AI 能力：

- LLM：负责分析、规划、文案、Prompt、评价。
- 多模态模型：负责理解商品图片和评价生成结果。
- 图片生成模型：负责生成营销图。
- 图片编辑模型：负责局部修改、背景替换。
- Embedding/RAG：可选，用于平台规则、品牌风格、历史案例检索。

## 11. Agent 架构

Agent 列表：

- Router Agent：判断用户当前意图，如新建项目、分析商品、生成创意方案、生成图片、修改图片、修改文案、导出素材、查看历史项目。
- Product Analysis Agent：理解商品本身，输出商品类别、卖点、目标人群、推荐风格和图片问题。
- Creative Planner Agent：生成营销创意方案，输出方案名称、画面构思、适用平台、视觉风格、文案方向和推荐理由。
- Prompt Engineer Agent：生成正向 Prompt、反向 Prompt、图生图参数建议、尺寸建议、风格约束和商品保真约束。
- Image Generation Tool：调用图片生成模型。它是工具，不是 Agent。
- Image Critic Agent：评价图片质量和营销价值，输出总分、分项评分、瑕疵说明、优化建议和是否推荐使用。
- Copywriting Agent：生成标题、卖点、小红书正文、朋友圈文案、淘宝详情页文案和标签。
- Revision Agent：理解用户修改意见，决定修改类型、修改目标、需要调用的工具、新 Prompt 和是否需要重新生成。
- Export Agent：整理最终素材，输出图片文件、文案文件、多平台尺寸版本、Markdown 报告和 ZIP 压缩包。

主工作流：

```text
用户上传商品图
  -> Product Analysis Agent
  -> Creative Planner Agent
  -> Prompt Engineer Agent
  -> Image Generation Tool
  -> Image Critic Agent
  -> Copywriting Agent
  -> Revision Agent / Export Agent
```

LangGraph 状态草案：

```python
class ProductShotState(TypedDict):
    user_id: str
    project_id: str
    product_images: list[str]
    product_name: str
    product_category: str | None
    product_selling_points: list[str]
    target_platform: str
    target_audience: str | None
    preferred_style: str | None
    product_analysis: dict | None
    creative_plans: list[dict]
    selected_plan: dict | None
    image_prompts: list[dict]
    generation_tasks: list[dict]
    generated_images: list[dict]
    image_reviews: list[dict]
    copywriting_results: dict | None
    revision_instruction: str | None
    export_files: list[str]
```

## 12. 数据模型草案

`user`：

- id
- username
- email
- password_hash
- created_at
- updated_at

`project`：

- id
- user_id
- product_name
- product_category
- target_platform
- target_audience
- preferred_style
- status
- created_at
- updated_at

`product_asset`：

- id
- project_id
- file_url
- file_type
- is_primary
- width
- height
- created_at

`product_analysis`：

- id
- project_id
- analysis_json
- created_at

`creative_plan`：

- id
- project_id
- plan_name
- plan_description
- target_platform
- visual_style
- selling_angle
- plan_json
- created_at

`generation_task`：

- id
- project_id
- plan_id
- prompt
- negative_prompt
- model_name
- status
- error_message
- created_at
- updated_at

`generated_image`：

- id
- task_id
- project_id
- image_url
- width
- height
- score
- is_selected
- created_at

`image_review`：

- id
- image_id
- overall_score
- product_clarity_score
- style_match_score
- commercial_value_score
- platform_fit_score
- defects_json
- suggestions_json
- created_at

`copywriting`：

- id
- project_id
- image_id
- title
- selling_points
- xiaohongshu_text
- moments_text
- taobao_text
- tags_json
- created_at

## 13. API 草案

创建项目：

```http
POST /api/projects
```

```json
{
  "product_name": "手工香薰蜡烛",
  "product_category": "家居香氛",
  "target_platform": "小红书",
  "target_audience": "年轻女性",
  "preferred_style": "温暖治愈风"
}
```

上传商品图：

```http
POST /api/projects/{project_id}/assets
```

启动 Agent 工作流：

```http
POST /api/projects/{project_id}/agent/run
```

```json
{
  "mode": "full_generation"
}
```

获取 Agent 执行状态：

```http
GET /api/projects/{project_id}/agent/status
```

```json
{
  "current_step": "image_review",
  "progress": 80,
  "message": "正在评价生成图片质量"
}
```

获取创意方案：

```http
GET /api/projects/{project_id}/creative-plans
```

选择创意方案并生成图片：

```http
POST /api/projects/{project_id}/generate-images
```

```json
{
  "plan_id": "plan_001",
  "count": 4
}
```

修改图片或文案：

```http
POST /api/projects/{project_id}/revise
```

```json
{
  "target_image_id": "img_001",
  "instruction": "背景更高级一点，商品再大一些，更适合小红书封面"
}
```

导出素材：

```http
POST /api/projects/{project_id}/export
```

```json
{
  "platforms": ["xiaohongshu", "moments"],
  "include_copywriting": true,
  "format": "zip"
}
```

## 14. 非功能需求

性能：

- 商品分析响应时间小于 10 秒。
- 创意方案生成小于 15 秒。
- 图片生成任务支持异步执行。
- 用户可实时查看生成进度。
- 支持任务失败重试。

可用性：

- 用户不需要学习 Prompt。
- 每一步都要有清晰提示。
- 生成失败要展示可理解的原因。
- 支持重新生成。
- 支持历史记录恢复。

安全：

- 用户图片隔离存储。
- 生成内容需进行基础安全审核。
- 禁止生成违法、侵权、虚假宣传内容。
- 不允许自动生成冒充官方认证的营销素材。
- 用户删除项目时同步删除相关图片。

成本控制：

- 图片生成任务需要限制次数。
- 同一项目的中间结果需要缓存。
- 失败任务需要避免无限重试。
- 评价 Agent 可以优先使用低成本模型。
- 导出和裁剪尽量用代码处理。

## 15. MVP 范围

必做：

- 商品图上传。
- 商品信息填写。
- 商品分析。
- 创意方案生成。
- 图片 Prompt 生成。
- 图片生成。
- 图片评价。
- 文案生成。
- 自然语言修改。
- 项目历史记录。

暂不做：

- 支付系统。
- 团队协作。
- 多店铺管理。
- 自动发布到平台。
- 复杂品牌资产库。
- 精细化局部编辑。
- 大规模批量生成。
- 电商平台 API 对接。

## 16. 项目亮点

- 不只是调用图片生成 API，而是解决“小商家如何获得一套可用营销素材”的完整问题。
- 多 Agent 分工明确，包括商品分析、创意策划、Prompt 生成、图片评价、文案生成、修改迭代和导出。
- 有完整业务闭环：上传商品 -> 分析商品 -> 生成创意 -> 生成图片 -> 评价质量 -> 生成文案 -> 用户修改 -> 导出素材。
- 有传统工程能力：用户系统、项目管理、文件存储、异步任务、状态流转、SSE/WebSocket、数据库设计和多平台导出。
- 有评价反馈机制，避免只生成不判断。

## 17. 开发优先级

第一阶段：基础工程

- 搭建前端页面。
- 搭建后端项目。
- 实现用户项目管理。
- 实现图片上传和存储。
- 实现项目历史记录。

第二阶段：Agent 工作流

- 商品分析 Agent。
- 创意策划 Agent。
- Prompt 生成 Agent。
- 文案生成 Agent。
- Agent 执行状态展示。

第三阶段：图片生成

- 接入图片生成 API。
- 实现异步生成任务。
- 保存生成结果。
- 支持多图展示。
- 支持重新生成。

第四阶段：评价和迭代

- 实现图片评价 Agent。
- 实现评分展示。
- 支持自然语言修改。
- 支持图片重新生成。
- 支持文案改写。

第五阶段：导出和包装

- 多尺寸导出。
- 文案复制。
- ZIP 打包。
- 示例项目。
- README。
- 部署上线。
- 录制演示视频。

## 18. 成功指标

用户体验：

- 用户能在 3 分钟内完成一次商品素材生成。
- 用户不需要自己编写 Prompt。
- 用户至少能获得 3 个不同创意方向。
- 用户能获得图片和文案的完整组合。
- 用户可以通过自然语言完成二次修改。

生成质量：

- 商品主体清晰。
- 商品没有明显变形。
- 图片风格符合用户选择。
- 文案和图片风格一致。
- 输出内容适合目标平台发布。

工程质量：

- Agent 流程状态可追踪。
- 图片生成任务异步执行。
- 失败任务可重试。
- 历史项目可恢复。
- 文件可正常导出。

## 19. 风险与解决方案

商品保真问题：

- 风险：生成图可能改变商品外观。
- 解决：优先使用图生图；Prompt 加入商品保真约束；评价 Agent 检查商品是否变形；对不合格结果降分。

生成成本较高：

- 风险：图片生成 API 成本较高。
- 解决：限制每次生成数量；使用异步任务；缓存中间结果；低成本模型先生成草稿；高质量模型只用于最终图。

用户输入过少：

- 风险：用户只上传图片，不知道怎么填写信息。
- 解决：Agent 自动识别商品；系统给出默认卖点建议；自动推荐目标人群和视觉风格。

图片质量不可控：

- 风险：生成结果不稳定。
- 解决：一次生成多张；评价 Agent 自动排序；支持重新生成；支持自然语言修改；保存高分 Prompt 模板。

项目容易显得像套壳：

- 风险：如果只是调用图片生成 API，项目价值不高。
- 解决：强调多 Agent 工作流；展示商品分析过程、创意方案、评分和修改机制；同时展示项目管理、任务队列、导出等工程能力。

## 20. 简历描述草案

产品版：

> 设计并实现一个面向小商家的商品营销图多 Agent 生成平台，支持商品图上传、商品语义分析、营销创意规划、图片生成 Prompt 构建、AIGC 图片生成、图片质量评价、营销文案生成与多平台素材导出。系统通过 Product Analysis Agent、Creative Planner Agent、Prompt Agent、Image Critic Agent、Copywriting Agent 等角色协作，将单次图片生成扩展为可规划、可评价、可迭代的内容生产工作流。

工程版：

> 基于 LangGraph 构建商品营销内容生成工作流，将商品分析、创意策划、图片生成、质量评估、文案生成和导出流程拆分为多个 Agent 节点；使用异步任务队列管理图片生成任务，通过状态机记录 Agent 执行进度，并结合多模态模型对生成图片进行商品清晰度、风格匹配度和营销价值评分，实现从商品图到营销素材包的一站式生成。

