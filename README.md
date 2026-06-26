# ProductShot Agent

面向轻量商家的 AI 商品营销素材工作台：上传一张普通商品图，系统完成原图理解、商品策略、创意方向、Prompt Pack、图片生成、质量评分、多平台文案、自然语言修改和 Markdown / JSON 导出。

这个项目不是单点图片生成器，而是一个围绕“商品营销内容生产”的可运行工作流。它的目标是让没有专业摄影和设计能力的小商家，也能从一张杂乱实拍图开始，快速得到一组更适合小红书、朋友圈、淘宝等平台发布的素材。

![ProductShot 工作台](docs/assets/studio-analysis.png)

## 它解决什么问题

很多小商家并不缺商品，而是缺少稳定生产营销内容的能力：

- 原图背景杂乱、构图随手拍，直接发布显得不专业。
- 不知道如何提炼卖点、选择视觉方向、写不同平台的文案。
- 直接使用图片生成工具时，需要反复写提示词、出图、判断结果。
- 生成图缺少质量评分、修改依据和可追踪的项目上下文。

ProductShot 把这些步骤收敛成一条连续的“商品素材生产线”：确定性代码负责项目、文件、状态、导出和 Provider 调度，LLM Agent 负责视觉理解、营销策略、创意规划、Prompt、评分、文案和修改意图。

## 效果示例

下面是一次真实流程中的输入与输出：左侧是普通门店环境下拍摄的玩偶原图，右侧是站内通过 DashScope 图片 Provider 生成的商品营销图。

| 原始商品图 | 生成效果图 |
| --- | --- |
| ![猫头鹰玩偶原图](docs/assets/sample-original.jpeg) | ![ProductShot 生成图](docs/assets/sample-generated.png) |

生成结果保留了白色毛绒主体、黑黄眼睛和红黄围巾等关键商品特征，同时去掉杂乱背景，形成更适合商品展示和社交平台发布的画面。

## 核心工作流

```text
创建项目
  -> 上传商品原图
  -> 原图理解：提取外观、材质、背景问题和保真约束
  -> 商品策略：理解卖点、人群、平台和视觉风格
  -> 方向规划：生成 3 个可选创意方向
  -> 用户选择方向
  -> Prompt Pack：只为选中方向生成提示词和负向约束
  -> 素材生成：调用图片 Provider 生成营销图
  -> 质量评价：评分、排序并推荐最佳图
  -> 发布文案：生成标题、卖点、小红书、朋友圈、淘宝和抖音文案
  -> 自然语言修改
  -> 导出 Markdown / JSON 素材报告
```

工作台采用连续式 `/studio` 体验，项目创建、分析、方案、生成、评分、文案和导出都在同一个上下文中完成，避免每一步跳转到不同页面。

![创意方向选择](docs/assets/studio-plans.png)

![生成素材与文案](docs/assets/studio-output-copy.png)

## 项目亮点

### 1. 面向真实业务闭环，而不是只做 Demo 出图

- 支持从商品信息、原图、平台、人群和风格偏好开始建项目。
- 先给出 3 个营销方向，让用户选择后再消耗图片生成资源。
- 每张生成图会经过质量评价，包含商品清晰度、商品一致性、风格匹配、商业价值和平台适配。
- 自动生成多平台文案和标签，最后可导出 Markdown / JSON 素材包。

### 2. 多 Agent 分工清晰

后端服务层编排多个职责明确的 Agent：

| Agent | 作用 |
| --- | --- |
| `VisualAnalysisAgent` | 理解原图外观、颜色、材质、可见文字、背景问题和商品保真约束 |
| `ProductAnalysisAgent` | 结合商品信息与视觉分析，提炼人群、卖点、平台策略和视觉风格 |
| `CreativePlannerAgent` | 生成 3 个可选营销创意方向 |
| `PromptEngineerAgent` | 将选中方向转成图片生成 Prompt Pack |
| `ImageCriticAgent` | 对生成图做营销质量评分并推荐最佳图 |
| `CopywritingAgent` | 生成标题、卖点、多平台发布文案和标签 |
| `RevisionAgent` | 将自然语言修改要求转换为修改计划和新 Prompt |

Agent 只处理适合 LLM 的模糊理解、生成、判断和表达任务；项目状态、文件存储、接口校验、导出报告和 Provider 调度仍由普通代码负责。

### 3. Provider 抽象便于本地演示和真实模型切换

- 默认 `mock` Provider 不需要 API Key，可以本地跑通完整流程。
- `dashscope` Text Provider 通过 DashScope SDK 调用多模态/文字推理。
- `dashscope` Image Provider 支持异步图片生成任务、轮询、下载和本地落盘。
- `openai` 图片 Provider 保留扩展骨架，便于后续接入其他图像模型。
- 模型配置页只调整非敏感配置，API Key 始终从后端系统环境变量读取。

![模型管理](docs/assets/model-settings.png)

### 4. 可观测的 Agent Trace

每个关键节点都会记录为持久化事件，包括：

- `step_key`
- Agent / Provider 名称
- 运行状态
- 摘要
- 结构化详情
- 错误信息
- 起止时间和耗时

这让慢模型调用、图片生成排队、评分失败、文案失败等问题可以在页面上直接定位，而不是只能看后端日志。

![流程诊断](docs/assets/agent-trace.png)

## 技术架构

| 模块 | 技术 |
| --- | --- |
| 前端 | Vue 3, TypeScript, Vite, Pinia, Vue Router, Element Plus |
| 后端 | FastAPI, SQLAlchemy, SQLite, Pydantic |
| 工作流 | 服务层编排多个 Agent，Provider 层隔离文字模型和图片生成模型 |
| 存储 | 本地 SQLite + uploads 文件目录 |
| 模型接入 | Mock, DashScope；OpenAI 图片 Provider 骨架预留 |
| 导出 | Markdown / JSON 素材报告 |

项目结构：

```text
.
├── backend/
│   ├── app/
│   │   ├── agents/        # 商品分析、创意、Prompt、评分、文案、修改 Agent
│   │   ├── api/           # FastAPI 路由
│   │   ├── providers/     # Text / Image Provider 抽象与实现
│   │   ├── services/      # 工作流编排
│   │   ├── storage/       # 上传文件保存
│   │   └── models/        # SQLAlchemy 数据模型
│   └── tests/
├── frontend/
│   └── src/
│       ├── views/         # 首页、项目工作台、模型管理
│       ├── stores/        # 项目流程状态
│       └── api/           # 后端 API Client
└── docs/
    ├── PRD.md
    └── assets/
```

## 快速启动

### 1. 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

后端默认运行在 `http://127.0.0.1:8000`，API 文档在 `http://127.0.0.1:8000/docs`。

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://127.0.0.1:5173`。

### 3. 默认 Mock 流程

默认情况下不需要真实模型 Key。Mock Provider 会复制上传原图或生成占位图，并返回结构化的分析、方案、评分和文案，适合本地演示完整产品闭环。

## 可选：接入 DashScope

如果要测试真实文字推理和图片生成，可以通过环境变量切换：

```bash
export TEXT_PROVIDER=dashscope
export IMAGE_PROVIDER=dashscope
export TEXT_MODEL=qwen3.7-plus
export DASHSCOPE_IMAGE_MODEL=wan2.7-image-pro
export DASHSCOPE_BASE_HTTP_API_URL=https://dashscope.aliyuncs.com/api/v1
export DASHSCOPE_API_KEY=your_api_key
```

注意：不要把真实 Key、个人专属 Base URL、Workspace ID、业务空间地址写入 `.env`、README、代码、测试或前端请求中。当前前端模型管理页只展示 Key 是否已在后端配置，并允许调整非敏感模型参数。

更多后端配置见 [backend/README.md](backend/README.md)。

## 验证方式

后端测试：

```bash
cd backend
pytest -q
```

前端构建：

```bash
cd frontend
npm run build
```

建议的手动验证路径：

1. 打开 `/studio`，创建商品项目并上传图片。
2. 运行原图理解，检查商品外观、材质、背景问题和保真约束。
3. 确认或修正原图理解结果后生成商品策略和 3 个创意方向。
4. 选择一个创意方向生成素材包。
5. 查看生成图、质量评分、推荐图、多平台文案和流程诊断。
6. 输入自然语言修改要求，最后导出 Markdown / JSON 报告。

## 当前边界

- 这是本地 MVP，不是生产级 SaaS。
- 默认 Mock 图片生成不代表真实商品图生成质量，只用于验证产品流程。
- 真实图片生成质量取决于所接入模型、原图质量、提示词和平台限制。
- OpenAI 图片 Provider 当前是扩展骨架，真实生产接入仍需要补齐模型调用和异常处理。
- 图片主体一致性、版权风险、平台合规、批量导出、账号体系和权限控制仍需要继续完善。
- 数据默认存储在本地 SQLite 和 uploads 目录，暂未实现云端存储。

## 下一步计划

- 补强图片生成任务的失败重试、状态解释和版本对比。
- 增加生成结果收藏、重生成、A/B 对比和批量导出。
- 支持更多平台尺寸和导出模板。
- 完善端到端演示数据，降低作品展示时的理解成本。
- 扩展工作流测试，覆盖 Agent 输出结构、Provider 降级和导出报告。

## 相关文档

- [产品需求文档](docs/PRD.md)
- [后端说明](backend/README.md)
- [前端说明](frontend/README.md)
