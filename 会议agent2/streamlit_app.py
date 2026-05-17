from __future__ import annotations

import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("MEETING_AGENT_API_BASE_URL", "http://127.0.0.1:8000")


def upload_meeting(title: str, organizer: str, uploaded_file) -> dict:
    files = {
        "audio_file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        ),
    }
    data = {"title": title, "organizer": organizer}
    response = requests.post(f"{API_BASE_URL}/meetings/upload", data=data, files=files, timeout=300)
    response.raise_for_status()
    return response.json()


def transcribe_meeting(meeting_id: str) -> dict:
    response = requests.post(f"{API_BASE_URL}/meetings/{meeting_id}/transcribe", timeout=1800)
    response.raise_for_status()
    return response.json()


def summarize_meeting(meeting_id: str) -> dict:
    response = requests.post(f"{API_BASE_URL}/meetings/{meeting_id}/summarize", timeout=1800)
    response.raise_for_status()
    return response.json()


def get_meeting(meeting_id: str) -> dict:
    response = requests.get(f"{API_BASE_URL}/meetings/{meeting_id}", timeout=60)
    response.raise_for_status()
    return response.json()


def render_string_list(title: str, items: list[str], empty_text: str = "暂无内容") -> None:
    st.markdown(f"#### {title}")
    if not items:
        st.caption(empty_text)
        return
    for item in items:
        st.markdown(f"- {item}")


def render_action_items(items: list[dict]) -> None:
    st.markdown("#### 待办事项")
    if not items:
        st.caption("暂无待办事项")
        return
    for index, item in enumerate(items, start=1):
        task = item.get("task", "") or "未命名任务"
        owner = item.get("owner", "") or "待定"
        deadline = item.get("deadline", "") or "待定"
        status = item.get("status", "") or "pending"
        st.markdown(
            f"**{index}. {task}**  \n"
            f"负责人：`{owner}` ｜ 截止时间：`{deadline}` ｜ 状态：`{status}`"
        )


def render_meeting_detail(detail: dict) -> None:
    summary_json = detail.get("summary_json", {}) or {}
    summary_check_json = detail.get("summary_check_json", {}) or {}

    st.subheader("任务概览")
    top1, top2, top3, top4 = st.columns(4)
    top1.metric("任务状态", detail.get("status", "-"))
    top2.metric("会议标题", detail.get("title", "-"))
    top3.metric("组织者", detail.get("organizer", "-"))
    top4.metric("Summary Stage", detail.get("summary_stage", "-"))

    st.caption(
        f"任务 ID：`{detail.get('meeting_id', '')}`  |  原始文件：`{detail.get('audio_file_name', '')}`"
    )
    st.caption(f"Summary Retry Count：`{detail.get('summary_retry_count', 0)}`")
    if detail.get("needs_human_review"):
        st.warning("当前总结结果需要人工复核。")

    overview_left, overview_right = st.columns([1.1, 1.4])

    with overview_left:
        st.markdown("### 纪要正文")
        summary_text = detail.get("summary_text", "")
        if summary_text:
            st.markdown(summary_text)
        else:
            st.info("当前还没有生成会议纪要。")

    with overview_right:
        st.markdown("### 结构化结果")
        st.markdown(f"**会议主题**：{summary_json.get('meeting_topic', '待提取') or '待提取'}")
        st.markdown(f"**一句话总结**：{summary_json.get('summary', '待生成') or '待生成'}")
        render_string_list("关键讨论点", summary_json.get("key_points", []), "暂无关键讨论点")
        render_string_list("决议事项", summary_json.get("decisions", []), "暂无决议事项")
        render_action_items(summary_json.get("action_items", []))
        render_string_list("风险", summary_json.get("risks", []), "暂无风险")
        render_string_list("待确认问题", summary_json.get("open_questions", []), "暂无待确认问题")

    st.markdown("---")
    bottom_left, bottom_right = st.columns(2)

    with bottom_left:
        st.markdown("### 转写文本")
        st.text_area(
            "transcript_text",
            detail.get("transcript_text", ""),
            height=320,
            label_visibility="collapsed",
        )

    with bottom_right:
        st.markdown("### 清洗后文本")
        st.text_area(
            "clean_transcript_text",
            detail.get("clean_transcript_text", ""),
            height=320,
            label_visibility="collapsed",
        )

    with st.expander("查看技术详情", expanded=False):
        st.write(f"本地路径：`{detail.get('stored_file_path', '')}`")
        st.write(f"OSS 对象：`{detail.get('oss_object_key', '')}`")
        st.json(summary_json)
        st.markdown("#### Summary Check")
        st.json(summary_check_json)

    error_message = detail.get("error_message", "")
    if error_message:
        st.error(error_message)


st.set_page_config(page_title="Meeting Agent 2", layout="wide")
st.title("Meeting Agent 2")
st.caption("上传会议音频，完成转写和总结，并以更易读的方式查看会议结果。")

with st.sidebar:
    st.header("服务配置")
    st.write(f"当前 API：`{API_BASE_URL}`")
    st.info("先启动 FastAPI：`uvicorn backend.api.api_server:app --reload`")

tab_upload, tab_query = st.tabs(["上传与处理", "查询任务"])

with tab_upload:
    st.subheader("上传会议音频")
    title = st.text_input("会议标题", value="Demo 会议")
    organizer = st.text_input("组织者", value="Codex")
    uploaded_file = st.file_uploader(
        "选择音频或视频文件",
        type=["wav", "mp3", "m4a", "mp4", "aac", "flac", "ogg"],
    )

    if "last_meeting_id" not in st.session_state:
        st.session_state["last_meeting_id"] = ""

    col1, col2, col3 = st.columns(3)

    if col1.button("上传", use_container_width=True, disabled=uploaded_file is None):
        try:
            result = upload_meeting(title, organizer, uploaded_file)
            st.session_state["last_meeting_id"] = result["meeting_id"]
            st.success(f"上传成功，任务 ID：{result['meeting_id']}")
        except requests.HTTPError as exc:
            st.error(f"上传失败：{exc.response.text}")
        except Exception as exc:
            st.error(f"上传失败：{exc}")

    meeting_id = st.text_input("任务 ID", value=st.session_state["last_meeting_id"])

    if col2.button("转写", use_container_width=True, disabled=not meeting_id):
        try:
            transcribe_meeting(meeting_id)
            st.success("转写完成")
        except requests.HTTPError as exc:
            st.error(f"转写失败：{exc.response.text}")
        except Exception as exc:
            st.error(f"转写失败：{exc}")

    if col3.button("总结", use_container_width=True, disabled=not meeting_id):
        try:
            summarize_meeting(meeting_id)
            st.success("总结完成")
        except requests.HTTPError as exc:
            st.error(f"总结失败：{exc.response.text}")
        except Exception as exc:
            st.error(f"总结失败：{exc}")

    if st.button("刷新当前任务详情", use_container_width=True, disabled=not meeting_id):
        try:
            detail = get_meeting(meeting_id)
            render_meeting_detail(detail)
        except requests.HTTPError as exc:
            st.error(f"查询失败：{exc.response.text}")
        except Exception as exc:
            st.error(f"查询失败：{exc}")

with tab_query:
    st.subheader("按任务 ID 查询")
    query_meeting_id = st.text_input("输入任务 ID", key="query_meeting_id")
    if st.button("查询", key="query_button", use_container_width=True, disabled=not query_meeting_id):
        try:
            detail = get_meeting(query_meeting_id)
            render_meeting_detail(detail)
        except requests.HTTPError as exc:
            st.error(f"查询失败：{exc.response.text}")
        except Exception as exc:
            st.error(f"查询失败：{exc}")
