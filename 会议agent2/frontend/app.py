"""会议转写的 Streamlit 演示页面。"""

from __future__ import annotations

import sys
from pathlib import Path

import requests
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config import load_frontend_config


def resolve_api_base_url() -> str:
    """返回配置中第一个可访问的 API 基础地址。"""
    config = load_frontend_config()
    candidates = config.get("api_base_urls", [])
    for base_url in candidates:
        normalized = str(base_url).rstrip("/")
        try:
            response = requests.get(f"{normalized}/health", timeout=2)
            response.raise_for_status()
            return normalized
        except requests.RequestException:
            continue
    if candidates:
        return str(candidates[0]).rstrip("/")
    return "http://127.0.0.1:8000"


API_BASE_URL = resolve_api_base_url()


def upload_meeting(title: str, organizer: str, meeting_category: str, uploaded_file) -> dict:
    """上传单个会议媒体文件并创建任务。"""
    files = {
        "audio_file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        ),
    }
    data = {"title": title, "organizer": organizer, "meeting_category": meeting_category}
    response = requests.post(f"{API_BASE_URL}/meetings/upload", data=data, files=files, timeout=300)
    response.raise_for_status()
    return response.json()


def transcribe_meeting(meeting_id: str) -> dict:
    """触发单个会议任务的转写。"""
    response = requests.post(f"{API_BASE_URL}/meetings/{meeting_id}/transcribe", timeout=1800)
    response.raise_for_status()
    return response.json()


def get_meeting(meeting_id: str) -> dict:
    """查询单个会议任务。"""
    response = requests.get(f"{API_BASE_URL}/meetings/{meeting_id}", timeout=60)
    response.raise_for_status()
    return response.json()


def render_meeting_detail(detail: dict) -> None:
    """渲染单个会议任务的详情面板。"""
    st.subheader("Task Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Status", detail.get("status", "-"))
    col2.metric("Title", detail.get("title", "-"))
    col3.metric("Category", detail.get("meeting_category", "-"))

    st.caption(f"File: `{detail.get('audio_file_name', '')}`")

    st.caption(f"Meeting ID: `{detail.get('meeting_id', '')}`")

    st.markdown("### 总结")
    st.text_area(
        "summary_text",
        detail.get("summary_text", ""),
        height=220,
        label_visibility="collapsed",
    )

    st.markdown("### 转写内容")
    st.text_area(
        "transcript_text",
        detail.get("transcript_text", ""),
        height=360,
        label_visibility="collapsed",
    )

    error_message = detail.get("error_message", "")
    if error_message:
        st.error(error_message)


def main() -> None:
    """渲染 Streamlit 应用。"""
    st.set_page_config(page_title="Meeting Agent 2", layout="wide")
    st.title("Meeting Agent 2")
    st.caption("Upload audio, run transcription, and review the recognized transcript.")

    with st.sidebar:
        st.header("Service")
        st.write(f"Current API: `{API_BASE_URL}`")
        st.info("Start FastAPI first: `uvicorn backend.app.api_server:app --reload`")

    tab_upload, tab_query = st.tabs(["Upload and Process", "Query Task"])

    with tab_upload:
        st.subheader("Upload Meeting Audio")
        title = st.text_input("Meeting Title", value="Demo Meeting")
        meeting_category = st.text_input("Meeting Category", value="project-a")
        organizer = st.text_input("Organizer", value="Codex")
        uploaded_file = st.file_uploader(
            "Choose an audio or video file",
            type=["wav", "mp3", "m4a", "mp4", "aac", "flac", "ogg"],
        )

        if "last_meeting_id" not in st.session_state:
            st.session_state["last_meeting_id"] = ""

        col1, col2 = st.columns(2)

        if col1.button("Upload", use_container_width=True, disabled=uploaded_file is None):
            try:
                result = upload_meeting(title, organizer, meeting_category, uploaded_file)
                st.session_state["last_meeting_id"] = result["meeting_id"]
                st.success(f"Upload complete. Meeting ID: {result['meeting_id']}")
            except requests.HTTPError as exc:
                st.error(f"Upload failed: {exc.response.text}")
            except Exception as exc:
                st.error(f"Upload failed: {exc}")

        meeting_id = st.text_input("Meeting ID", value=st.session_state["last_meeting_id"])

        if col2.button("Transcribe", use_container_width=True, disabled=not meeting_id):
            try:
                detail = transcribe_meeting(meeting_id)
                st.success("Transcription complete.")
                render_meeting_detail(detail)
            except requests.HTTPError as exc:
                st.error(f"Transcription failed: {exc.response.text}")
            except Exception as exc:
                st.error(f"Transcription failed: {exc}")

        if st.button("Refresh Current Task", use_container_width=True, disabled=not meeting_id):
            try:
                detail = get_meeting(meeting_id)
                render_meeting_detail(detail)
            except requests.HTTPError as exc:
                st.error(f"Query failed: {exc.response.text}")
            except Exception as exc:
                st.error(f"Query failed: {exc}")

    with tab_query:
        st.subheader("Query by Meeting ID")
        query_meeting_id = st.text_input("Meeting ID", key="query_meeting_id")
        if st.button("Query", key="query_button", use_container_width=True, disabled=not query_meeting_id):
            try:
                detail = get_meeting(query_meeting_id)
                render_meeting_detail(detail)
            except requests.HTTPError as exc:
                st.error(f"Query failed: {exc.response.text}")
            except Exception as exc:
                st.error(f"Query failed: {exc}")


if __name__ == "__main__":
    main()
