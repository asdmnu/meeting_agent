# 会议助手 2

Meeting Agent 2 当前聚焦会议音视频的上传、转写和查询，提供一条尽量简单的识别结果链路。项目后端基于 FastAPI，前端基于 Streamlit，使用 PostgreSQL 持久化任务数据，并通过 OSS + MCP 完成语音转写。

项目运行时使用两类配置：

- 普通配置放在仓库内的 YAML 配置文件
- 密钥和敏感信息放在 `.env`

## 功能概览

- 上传会议音视频并创建任务
- 上传原始文件到 OSS
- 通过 MCP 语音识别服务完成转写
- 查询任务状态和转写结果
- 支持 Docker Compose 一键部署

## 技术栈

- Python
- FastAPI
- Streamlit
- PostgreSQL
- DashScope
- OSS
- MCP

## 项目结构

```text
.
├── backend/
│   ├── app/
│   ├── config/
│   ├── core/
│   ├── loaders/
│   ├── services/
│   └── stores/
├── data/
├── frontend/
├── logs/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── streamlit_app.py
```

## 接口能力

- `POST /meetings/upload`
- `POST /meetings/{meeting_id}/transcribe`
- `GET /meetings/{meeting_id}`
- `GET /health`

## 配置说明

普通配置文件：

- [backend/config/app.yml](D:/agent项目/会议agent2/backend/config/app.yml)
- [backend/config/postgres.yml](D:/agent项目/会议agent2/backend/config/postgres.yml)
- [backend/config/mcp.yml](D:/agent项目/会议agent2/backend/config/mcp.yml)
- [frontend/config/app.yml](D:/agent项目/会议agent2/frontend/config/app.yml)

敏感信息放在：

- [\.env](D:/agent项目/会议agent2/.env)

当前 `.env` 只保留这些秘密配置：

- `MCP_API_KEY`
- `OSS_ACCESS_KEY_ID`
- `OSS_ACCESS_KEY_SECRET`
- `OSS_BUCKET_NAME`
- `OSS_ENDPOINT`
- `OSS_REGION`

## 本地启动

先补全 `.env` 中的密钥，再安装依赖：

```bash
pip install -r requirements.txt
```

启动后端：

```bash
uvicorn backend.app.api_server:app --reload
```

另开一个终端启动前端：

```bash
streamlit run frontend/app.py
```

启动后可以访问：

- API 文档: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 健康检查: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- 前端页面: [http://127.0.0.1:8501](http://127.0.0.1:8501)

## Docker 部署

确认配置文件和 `.env` 填写完成后，在项目根目录执行：

```bash
docker compose up --build
```

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

## 提交前注意

- 不要提交真实密钥或已填写的私有配置
- 建议确认 `.gitignore` 已覆盖本地缓存、日志和上传文件
- 如果仓库已经包含真实密钥，请先轮换密钥再公开仓库
