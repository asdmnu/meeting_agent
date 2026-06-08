from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from backend.app.schemas import MeetingDetail, MeetingTranscribeResponse, MeetingUploadResponse
from backend.core.config import load_app_config
from backend.core.paths import get_abs_path
from backend.flows.meeting_analysis.graph import meeting_analysis_graph
from backend.services.mcp_transcription_service import transcription_service
from backend.services.oss_service import oss_service
from backend.stores.meeting_store import MeetingStore


class MeetingService:
    """处理会议上传、转写和查询的应用服务。"""

    def __init__(self) -> None:
        app_config = load_app_config()
        self._upload_dir = Path(get_abs_path(app_config["upload_dir"]))
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        self._meeting_store = MeetingStore()

    def get_meeting(self, meeting_id: str) -> MeetingDetail | None:
        """根据 ID 返回单个会议任务。"""
        meeting = self._meeting_store.get_meeting(meeting_id)
        if meeting is None:
            return None
        return MeetingDetail(
            meeting_id=meeting.meeting_id,
            title=meeting.title,
            meeting_category=meeting.meeting_category,
            audio_file_name=meeting.audio_file_name,
            transcript_text=meeting.transcript_text,
            summary_text=meeting.summary_text,
            error_message=meeting.error_message,
            status=meeting.status,
            created_at=meeting.created_at,
        )

    def upload_meeting(
        self,
        title: str,
        organizer: str,
        meeting_category: str,
        audio_file: UploadFile,
    ) -> MeetingUploadResponse:
        """将上传文件保存到本地和远端，并创建任务记录。"""
        del organizer
        normalized_category = meeting_category.strip()

        meeting_id = str(uuid4())
        safe_name = Path(audio_file.filename or "audio.bin").name
        stored_path = self._upload_dir / f"{meeting_id}_{safe_name}"
        with stored_path.open("wb") as buffer:
            while chunk := audio_file.file.read(1024 * 1024):
                buffer.write(chunk)

        oss_object_key = f"meetings/{meeting_id}/{safe_name}"
        oss_service.upload_file(str(stored_path), oss_object_key)
        meeting = self._meeting_store.create_meeting(
            meeting_id,
            title,
            normalized_category,
            safe_name,
            str(stored_path),
            oss_object_key,
        )
        return MeetingUploadResponse(
            meeting_id=meeting.meeting_id,
            title=meeting.title,
            meeting_category=meeting.meeting_category,
            status=meeting.status,
            original_file_name=meeting.audio_file_name,
            created_at=meeting.created_at,
        )

    def transcribe_meeting_audio(self, meeting_id: str) -> MeetingTranscribeResponse:
        """从 OSS 获取已上传文件并保存转写结果。"""
        meeting = self._meeting_store.get_meeting(meeting_id)
        if meeting is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        try:
            if not meeting.oss_object_key:
                raise ValueError("Missing oss_object_key for meeting")
            file_url = oss_service.signed_get_url(meeting.oss_object_key, expires_seconds=3600)
            raw_transcript_text = transcription_service.transcribe_audio(file_url)
            transcript_text = self._clean_transcript_text(raw_transcript_text)
        except Exception as exc:
            updated = self._meeting_store.update_transcription_result(meeting_id, "", "failed", str(exc))
            if updated is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

        updated = self._meeting_store.update_transcription_result(
            meeting_id,
            transcript_text,
            "transcribed",
            "",
        )
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

        history_summaries = self._meeting_store.get_recent_summaries_by_category(
            meeting_category=updated.meeting_category,
            current_meeting_id=updated.meeting_id,
            limit=2,
        )
        history_context = "\n\n".join(
            f"历史会议总结 {index}:\n{summary}"
            for index, summary in enumerate(history_summaries, start=1)
        )

        analysis_state = meeting_analysis_graph.invoke(
            {
                "meeting_id": updated.meeting_id,
                "meeting_category": updated.meeting_category,
                "transcript_text": updated.transcript_text,
                "history_context": history_context,
            }
        )
        summary_text = str(analysis_state.get("summary_text", "")).strip()
        if summary_text:
            updated = self._meeting_store.update_summary_result(updated.meeting_id, summary_text) or updated

        return MeetingTranscribeResponse(
            meeting_id=updated.meeting_id,
            status=updated.status,
            transcript_text=updated.transcript_text,
            summary_text=updated.summary_text,
        )

    def _clean_transcript_text(self, transcript_text: str) -> str:
        """进行轻量清洗，并且只保存清洗后的转写内容。"""
        text = transcript_text.replace("\r\n", "\n").replace("\r", "\n").strip()
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]

        deduped_lines: list[str] = []
        for line in lines:
            if deduped_lines and deduped_lines[-1] == line:
                continue
            deduped_lines.append(line)

        return "\n".join(deduped_lines).strip()


meeting_service = MeetingService()
