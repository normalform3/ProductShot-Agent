# ProductShot Agent Backend

FastAPI 后端，提供项目管理、图片上传、原图视觉理解、3 个创意方向规划、选中方向生成素材包、评分、文案、修改和导出 API。

## 安装

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 启动

```bash
uvicorn app.main:app --reload
```

服务默认运行在 `http://127.0.0.1:8000`。

## 环境变量

- `DATABASE_URL`：默认 `sqlite:///backend/data/productshot.db`。
- `IMAGE_PROVIDER`：默认 `mock`，可选 `mock`、`openai`、`dashscope`。
- `TEXT_PROVIDER`：默认 `mock`，可选 `mock`、`dashscope`。
- `TEXT_MODEL`：文字/多模态推理模型，默认 `qwen3.7-plus`。
- `OPENAI_API_KEY`：OpenAI 图片生成 Provider 骨架预留。
- `DASHSCOPE_API_KEY`：百炼 API Key，只从系统环境变量读取，不要写入代码或提交到仓库。
- `DASHSCOPE_BASE_HTTP_API_URL`：百炼 SDK base URL，默认 `https://dashscope.aliyuncs.com/api/v1`。
- `DASHSCOPE_TEXT_BASE_URL`：兼容旧配置名；未设置 `DASHSCOPE_BASE_HTTP_API_URL` 时会作为 SDK base URL 使用。
- `DASHSCOPE_IMAGE_MODEL`：百炼文生图模型，默认 `wan2.7-image-pro`。
- `DASHSCOPE_IMAGE_GENERATION_URL`：兼容旧前端字段；当前 SDK 调用会同步作为 base URL 使用。
- `DASHSCOPE_WORKSPACE_ID`：可选，RAM 子账号或业务空间隔离场景使用。
- `MODEL_REQUEST_TIMEOUT`：模型 API 请求超时时间，默认 `180` 秒。
- `CORS_ORIGINS`：前端允许来源。

开发阶段使用百炼时，只需要在本机或部署环境设置变量，例如：

```bash
export TEXT_PROVIDER=dashscope
export IMAGE_PROVIDER=dashscope
export TEXT_MODEL=qwen3.7-plus
export DASHSCOPE_IMAGE_MODEL=wan2.7-image-pro
export DASHSCOPE_BASE_HTTP_API_URL=https://dashscope.aliyuncs.com/api/v1
```

不要在 `.env`、README、代码、测试或前端请求中写入真实 Key、个人专属 Base URL、Workspace ID 或业务空间地址。前端模型管理页只展示 Key 是否已配置，并允许调整非敏感模型配置。

## Mock 说明

MVP 默认使用 `MockImageProvider`。如果项目上传了原图，Mock 会复制原图并生成多个版本文件；如果没有原图，则生成 SVG 占位图。真实图片生成模型可以在 `app/providers/` 中替换。

## 主要工作流接口

- `POST /api/projects/{project_id}/agent/plan`：执行原图理解、商品策略和 3 个创意方向生成，不创建图片任务。
- `GET /api/projects/{project_id}/creative-plans`：获取用户可选择的 3 个方向。
- `POST /api/projects/{project_id}/creative-plans/{plan_id}/generate-pack`：只基于选中方向生成图片、评分、推荐图和配套文案。
