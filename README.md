# ProductShot Agent

ProductShot Agent 是一个面向小商家的商品营销内容生成平台。它的目标不是简单调用图片生成 API，而是把一张普通商品图转化为可发布的营销素材包，包括商品场景图、社媒封面、商品卖点文案、平台发布文案和多平台导出文件。

项目核心价值是把“小商家自己想创意、写提示词、反复生成、自己判断效果”的过程，变成一个可追踪、可评价、可迭代的多 Agent 内容生产工作流。

## 当前阶段

当前仓库已实现本地可运行 MVP：

- 后端：FastAPI + SQLAlchemy + SQLite + Mock ImageProvider。
- 前端：Vue 3 + TypeScript + Vite + Pinia + Vue Router + Element Plus。
- 默认不依赖真实图片生成 API，无 Key 也可以跑完整演示流程。

## 文档

- [产品需求文档](docs/PRD.md)
- [后端说明](backend/README.md)
- [前端说明](frontend/README.md)

## 快速启动

后端：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

访问：

- 前端：http://127.0.0.1:5173
- 后端：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/docs

## 一句话介绍

ProductShot Agent 能将一张普通商品图自动转化为多风格商品营销图、社媒封面、商品卖点文案和平台发布素材，并通过多 Agent 工作流实现创意规划、图片生成、质量评价和迭代修改。
# ProductShot-Agent
