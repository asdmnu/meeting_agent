from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from langsmith import traceable, tracing_context

from backend.api.schemas import (
    MeetingDetail,
    MeetingSummarizeResponse,
    MeetingTranscribeResponse,
    MeetingUploadResponse,
)
from backend.core.paths import get_abs_path
from backend.graphs.meeting_summary.graph import meeting_summary_graph
from backend.services.mcp_transcription_service import transcription_service
from backend.services.oss_service import oss_service
from backend.stores.meeting_store import MeetingStore


class MeetingService:
    def __init__(self) -> None:
        self._upload_dir = Path(get_abs_path("data/uploads"))
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        self._meeting_store = MeetingStore()
        self._summary_thread_id = "meeting-global-memory"

    def get_meeting(self, meeting_id: str) -> MeetingDetail | None:
        meeting = self._meeting_store.get_meeting(meeting_id)
        if meeting is None:
            return None
        return MeetingDetail(
            meeting_id=meeting.meeting_id,
            title=meeting.title,
            organizer=meeting.organizer,
            audio_file_name=meeting.audio_file_name,
            stored_file_path=meeting.stored_file_path,
            oss_object_key=meeting.oss_object_key,
            transcript_text=meeting.transcript_text,
            clean_transcript_text=meeting.clean_transcript_text,
            summary_json=meeting.summary_json,
            summary_text=meeting.summary_text,
            summary_stage=meeting.summary_stage,
            summary_check_json=meeting.summary_check_json,
            summary_retry_count=meeting.summary_retry_count,
            needs_human_review=meeting.needs_human_review,
            error_message=meeting.error_message,
            status=meeting.status,
            created_at=meeting.created_at,
        )

    def upload_meeting(self, title: str, organizer: str, audio_file: UploadFile) -> MeetingUploadResponse:
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
            organizer,
            safe_name,
            str(stored_path),
            oss_object_key,
        )
        return MeetingUploadResponse(
            meeting_id=meeting.meeting_id,
            title=meeting.title,
            status=meeting.status,
            original_file_name=meeting.audio_file_name,
            stored_file_path=meeting.stored_file_path,
            created_at=meeting.created_at,
        )

    def transcribe_meeting_audio(self, meeting_id: str) -> MeetingTranscribeResponse:
        meeting = self._meeting_store.get_meeting(meeting_id)
        if meeting is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        try:
            if not meeting.oss_object_key:
                raise ValueError("Missing oss_object_key for meeting")
            file_url = oss_service.signed_get_url(meeting.oss_object_key, expires_seconds=3600)
            transcript_text = transcription_service.transcribe_audio(file_url)
        except Exception as exc:
            updated = self._meeting_store.update_transcription_result(meeting_id, "", "failed", str(exc))
            if updated is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        updated = self._meeting_store.update_transcription_result(
            meeting_id,
            transcript_text,
            "processing_summary",
            "",
        )
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        return MeetingTranscribeResponse(meeting_id=updated.meeting_id, status=updated.status, transcript_text=updated.transcript_text)

    @traceable(name="meeting_summary")
    def summarize_meeting(self, meeting_id: str) -> MeetingSummarizeResponse:
        meeting = self._meeting_store.get_meeting(meeting_id)
        if meeting is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        if not meeting.transcript_text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No transcript text, please transcribe first")

        project_name = os.getenv("LANGSMITH_PROJECT", "meeting-agent2")
        metadata = {
            "meeting_id": meeting_id,
            "title": meeting.title,
            "organizer": meeting.organizer,
            "status": meeting.status,
            "thread_id": self._summary_thread_id,
        }

        try:
            with tracing_context(
                project_name=project_name,
                metadata=metadata,
                enabled=True,
            ):
                graph_result = meeting_summary_graph.invoke(
                    {
                        "meeting_id": meeting_id,
                        "transcript_text": meeting.transcript_text,
                        "clean_transcript_text": meeting.clean_transcript_text,
                        "summary_json": meeting.summary_json,
                        "summary_text": meeting.summary_text,
                        "validation_result": meeting.summary_check_json,
                        "retry_count": 0,
                        "max_retries": 2,
                        "summary_stage": "prepare",
                        "needs_human_review": False,
                        "error_message": "",
                    },
                    config={"configurable": {"thread_id": self._summary_thread_id}},
                )
            clean_transcript_text = graph_result["clean_transcript_text"]
            summary_json = graph_result["summary_json"]
            summary_text = graph_result["summary_text"]
            summary_stage = graph_result["summary_stage"]
            summary_check_json = graph_result["validation_result"]
            summary_retry_count = graph_result["retry_count"]
            needs_human_review = graph_result["needs_human_review"]
            final_status = "review_required" if needs_human_review else "done"
        except Exception as exc:
            updated = self._meeting_store.update_summary_result(
                meeting_id,
                "",
                {},
                "",
                "failed",
                {},
                0,
                False,
                "failed",
                str(exc),
            )
            if updated is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        updated = self._meeting_store.update_summary_result(
            meeting_id,
            clean_transcript_text,
            summary_json,
            summary_text,
            summary_stage,
            summary_check_json,
            summary_retry_count,
            needs_human_review,
            final_status,
            "",
        )
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        return MeetingSummarizeResponse(
            meeting_id=updated.meeting_id,
            status=updated.status,
            clean_transcript_text=updated.clean_transcript_text,
            summary_json=updated.summary_json,
            summary_text=updated.summary_text,
            summary_stage=updated.summary_stage,
            summary_check_json=updated.summary_check_json,
            summary_retry_count=updated.summary_retry_count,
            needs_human_review=updated.needs_human_review,
        )


meeting_service = MeetingService()
