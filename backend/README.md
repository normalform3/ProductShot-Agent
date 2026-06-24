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
- `OPENAI_API_KEY`：OpenAI 图片生成 Provider 骨架预留。
- `DASHSCOPE_API_KEY`：DashScope 图片生成 Provider 骨架预留。
- `CORS_ORIGINS`：前端允许来源。

## Mock 说明

MVP 默认使用 `MockImageProvider`。如果项目上传了原图，Mock 会复制原图并生成多个版本文件；如果没有原图，则生成 SVG 占位图。真实图片生成模型可以在 `app/providers/` 中替换。

