# ProductShot Agent Backend

FastAPI 后端，提供项目管理、图片上传、本地 Mock 图片生成、Agent 工作流、评分、文案、修改和导出 API。

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
- `TEXT_MODEL`：文字推理模型，默认 `qwen3.7plus`。
- `OPENAI_API_KEY`：OpenAI 图片生成 Provider 骨架预留。
- `DASHSCOPE_API_KEY`：百炼 API Key，只从系统环境变量读取，不要写入代码或提交到仓库。
- `DASHSCOPE_TEXT_BASE_URL`：百炼 OpenAI 兼容 Chat base URL，默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`。
- `DASHSCOPE_IMAGE_MODEL`：百炼文生图模型，默认 `wan2.6-t2i`。
- `DASHSCOPE_IMAGE_GENERATION_URL`：百炼文生图同步接口 URL。
- `DASHSCOPE_WORKSPACE_ID`：可选，RAM 子账号或业务空间隔离场景使用。
- `MODEL_REQUEST_TIMEOUT`：模型 API 请求超时时间，默认 `60` 秒。
- `CORS_ORIGINS`：前端允许来源。

开发阶段使用百炼时，只需要在本机或部署环境设置变量，例如：

```bash
export TEXT_PROVIDER=dashscope
export IMAGE_PROVIDER=dashscope
export TEXT_MODEL=qwen3.7plus
export DASHSCOPE_IMAGE_MODEL=wan2.6-t2i
```

不要在 `.env`、README、代码或前端请求中写入真实 Key。前端模型管理页只展示 Key 是否已配置，并允许调整非敏感模型配置。

## Mock 说明

MVP 默认使用 `MockImageProvider`。如果项目上传了原图，Mock 会复制原图并生成多个版本文件；如果没有原图，则生成 SVG 占位图。真实图片生成模型可以在 `app/providers/` 中替换。
