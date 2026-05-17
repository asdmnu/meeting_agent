# Meeting Agent

Meeting Agent 是一个面向公司会议场景的智能纪要项目。当前阶段已经打通了上传、落库、转码和转写骨架，下一步将接入真实的 FunASR 转写能力和后续纪要总结能力。

## 当前目录

```text
.
├── backend/        后端服务、配置、接口、存储访问、业务逻辑
├── data/
│   ├── uploads/    原始上传文件
│   └── converted/  ffmpeg 转码后的标准音频
├── frontend/       前端预留目录
├── logs/           日志目录
├── requirements.txt
├── .env.example
└── README.md
```

## 当前能力

- 上传会议音频或视频并保存到 `data/uploads/`
- 将会议元信息写入 PostgreSQL
- 查询会议记录和当前处理状态
- 调用 ffmpeg 将原始文件转成标准 wav 音频
- 将转码结果写回 `converted_file_path`
- 提供会议转写接口骨架
- 将转写文本写回 `transcript_text`

## 当前接口

- `GET /health`
- `POST /meetings/upload`
- `POST /meetings/{meeting_id}/convert`
- `POST /meetings/{meeting_id}/transcribe`
- `GET /meetings/{meeting_id}`

## 当前流程

1. 上传会议媒体文件
2. 写入数据库，状态设为 `uploaded`
3. 调用转码接口
4. ffmpeg 输出标准音频到 `data/converted/`
5. 回写 `converted_file_path`，状态更新为 `processing_asr`
6. 调用转写接口
7. 回写 `transcript_text`，状态更新为 `processing_summary`

## 说明

- `stored_file_path` 表示原始上传文件路径
- `converted_file_path` 表示 ffmpeg 转码后的输出路径
- `transcript_text` 当前已接好字段和接口，默认还是占位实现
- 当前机器已可用 `ffmpeg`

## 下一步

- 接入真实 FunASR 转写
- 增加说话人、术语纠错、错误处理
- 接入通义千问生成会议纪要
