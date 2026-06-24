# ProductShot Agent Frontend

Vue 3 + TypeScript + Vite 前端，使用 Pinia、Vue Router、Axios 和 Element Plus。

## 安装

```bash
cd frontend
npm install
```

## 启动

```bash
npm run dev
```

默认访问 `http://127.0.0.1:5173`。

## 环境变量

可在 `frontend/.env.local` 配置：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 页面

- 首页：产品定位和 Agent 流程。
- 创建项目页：填写商品信息并上传商品图。
- Agent 工作流页：运行商品分析和创意方案。
- 创意方案页：选择方案并生成图片。
- 生成结果页：查看原图、生成图、评分、文案、修改和导出。
- 历史项目页：查看本地项目列表。

