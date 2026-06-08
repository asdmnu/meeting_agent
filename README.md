# 会议助手 2

Meeting Agent 2 是一个面向会议场景的智能纪要项目，提供上传、转写、总结和查询的完整链路。项目后端基于 FastAPI，前端基于 Streamlit，使用 PostgreSQL 持久化任务数据，并通过 OSS + MCP 完成语音转写。

当前总结模块已经重构为基于 LangGraph 的总结 agent，不再是一次模型调用直接出结果，而是通过清洗、结构化提取、校验、修复和渲染的闭环流程生成会议纪要。

## 功能概览

- 上传会议音频并创建任务
- 上传原始文件到 OSS
- 通过 MCP 语音识别服务完成转写
- 通过 LangGraph 总结 agent 生成结构化纪要和正文纪要
- 查询任务状态、转写结果和总结结果
- 支持 LangSmith 观测总结图流程
- 支持 Docker Compose 一键部署

## 技术栈

- Python
- FastAPI
- Streamlit
- PostgreSQL
- LangChain
- LangGraph
- LangSmith
- DashScope / Qwen
- OSS
- MCP

## 项目结构

```text
.
├── backend/
│   ├── api/
│   ├── config/
│   ├── core/
│   ├── graphs/
│   ├── loaders/
│   ├── models/
│   ├── prompts/
│   ├── services/
│   └── stores/
├── data/
│   └── uploads/
├── logs/
├── .env.example
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── streamlit_app.py
```

## 接口能力

- `POST /meetings/upload`
- `POST /meetings/{meeting_id}/transcribe`
- `POST /meetings/{meeting_id}/summarize`
- `GET /meetings/{meeting_id}`
- `GET /health`

## 总结 Agent 流程

会议总结不是一次模型调用直接完成，而是一个 LangGraph 工作流：

- `prepare_summary`
- `clean_transcript`
- `extract_summary`
- `validate_summary`
- `repair_summary`（必要时循环）
- `render_summary`
- `finalize_summary`

同时，项目还维护“最近 5 次会议”的短期共享记忆，用于降低会议之间的内容串场问题。

## 环境变量

先复制环境变量模板：

```bash
cp .env.example .env
```

至少需要配置这些变量：

```env
DASHSCOPE_API_KEY=your_dashscope_api_key
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=meeting_agent2
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
OSS_ACCESS_KEY_ID=your_oss_access_key_id
OSS_ACCESS_KEY_SECRET=your_oss_access_key_secret
OSS_BUCKET_NAME=meetingagent
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_REGION=cn-beijing
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=meeting-agent2
MEETING_AGENT_API_BASE_URL=http://127.0.0.1:8000
```

## 本地启动

安装依赖：

```bash
pip install -r requirements.txt
```

启动后端：

```bash
uvicorn backend.api.api_server:app --reload
```

另开一个终端启动前端：

```bash
streamlit run streamlit_app.py
```

启动后可以访问：

- API 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/health>
- 前端页面：<http://127.0.0.1:8501>

## Docker 部署

确保已经准备好 `.env`，然后在项目根目录执行：

```bash
docker compose up --build
```

启动后可以访问：

- API 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/health>
- 前端页面：<http://127.0.0.1:8501>

后台启动：

```bash
docker compose up --build -d
```

停止服务：

```bash
docker compose down
```

停止服务并删除数据库卷：

```bash
docker compose down -v
```

## LangSmith 观测

项目已接入 LangSmith，总结接口在执行 LangGraph 总结流程时会上报 trace。

只要配置好：

- `LANGSMITH_API_KEY`
- `LANGSMITH_TRACING=true`
- `LANGSMITH_PROJECT`

然后调用 `/meetings/{meeting_id}/summarize`，就可以在 LangSmith 中看到图流程、模型调用和相关 metadata。

## 上传到 GitHub 前的注意事项

- 不要提交 `.env`
- 建议确认 `.gitignore` 已覆盖本地缓存、日志和上传文件
- 如果仓库已经包含真实密钥，请先轮换密钥再公开仓库

## 后续可扩展方向

- 持久化 LangGraph checkpointer，而不是仅使用内存版本
- 为总结结果增加自动评测集
- 增加会议记忆的可视化调试界面
- 增加异步任务队列和后台处理能力
