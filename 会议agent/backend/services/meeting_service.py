"""会议任务服务。"""

from pathlib import Path
from subprocess import CalledProcessError
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from backend.api.schemas import (
    MeetingConvertResponse,
    MeetingDetail,
    MeetingSummarizeResponse,
    MeetingTranscribeResponse,
    MeetingUploadResponse,
)
from backend.core.paths import get_abs_path
from backend.services.audio_service import audio_service
from backend.services.summary_service import summary_service
from backend.services.transcription_service import transcription_service
from backend.stores.meeting_store import MeetingStore


class MeetingService:
    """会议任务服务。"""

    def __init__(self) -> None:
        self._upload_dir = Path(get_abs_path("data/uploads"))
        self._converted_dir = Path(get_abs_path("data/converted"))
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        self._converted_dir.mkdir(parents=True, exist_ok=True)
        self._meeting_store = MeetingStore()

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
            converted_file_path=meeting.converted_file_path,
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
        audio_file: UploadFile,
    ) -> MeetingUploadResponse:
        meeting_id = str(uuid4())
        safe_name = Path(audio_file.filename or "audio.bin").name
        stored_name = f"{meeting_id}_{safe_name}"
        stored_path = self._upload_dir / stored_name

        with stored_path.open("wb") as buffer:
            while chunk := audio_file.file.read(1024 * 1024):
                buffer.write(chunk)

        meeting = self._meeting_store.create_meeting(
            meeting_id=meeting_id,
            title=title,
            organizer=organizer,
            audio_file_name=safe_name,
            stored_file_path=str(stored_path),
            converted_file_path="",
        )
        return MeetingUploadResponse(
            meeting_id=meeting.meeting_id,
            title=meeting.title,
            status=meeting.status,
            original_file_name=meeting.audio_file_name,
            stored_file_path=meeting.stored_file_path,
            converted_file_path=meeting.converted_file_path,
            created_at=meeting.created_at,
        )

    def convert_meeting_audio(self, meeting_id: str) -> MeetingConvertResponse:
        meeting = self._meeting_store.get_meeting(meeting_id)
        if meeting is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

        if not meeting.stored_file_path:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No source audio file")

        target_path = audio_service.build_converted_path(meeting_id, meeting.audio_file_name)

        try:
            audio_service.convert_to_wav(meeting.stored_file_path, str(target_path))
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ffmpeg is not installed or not available in PATH",
            ) from exc
        except CalledProcessError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=exc.stderr.strip() or "Audio conversion failed",
            ) from exc

        updated_meeting = self._meeting_store.update_conversion_result(
            meeting_id=meeting_id,
            converted_file_path=str(target_path),
            status="processing_asr",
        )
        if updated_meeting is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

        return MeetingConvertResponse(
            meeting_id=updated_meeting.meeting_id,
            status=updated_meeting.status,
            converted_file_path=updated_meeting.converted_file_path,
        )

    def transcribe_meeting_audio(self, meeting_id: str) -> MeetingTranscribeResponse:
        meeting = self._meeting_store.get_meeting(meeting_id)
        if meeting is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

        if not meeting.converted_file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No converted audio file, please convert first",
            )

        try:
            transcript_text = transcription_service.transcribe_audio(meeting.converted_file_path)
        except FileNotFoundError as exc:
            updated_meeting = self._meeting_store.update_transcription_result(
                meeting_id=meeting_id,
                transcript_text="",
                error_message=str(exc),
                status="failed",
            )
            if updated_meeting is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

        updated_meeting = self._meeting_store.update_transcription_result(
            meeting_id=meeting_id,
            transcript_text=transcript_text,
            error_message="",
            status="processing_summary",
        )
        if updated_meeting is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

        return MeetingTranscribeResponse(
            meeting_id=updated_meeting.meeting_id,
            status=updated_meeting.status,
            transcript_text=updated_meeting.transcript_text,
        )

    def summarize_meeting(self, meeting_id: str) -> MeetingSummarizeResponse:
        meeting = self._meeting_store.get_meeting(meeting_id)
        if meeting is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

        if not meeting.transcript_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcript text, please transcribe first",
            )

        summary_text = summary_service.summarize_transcript(meeting.transcript_text)
        updated_meeting = self._meeting_store.update_summary_result(
            meeting_id=meeting_id,
            summary_text=summary_text,
            error_message="",
            status="done",
        )
        if updated_meeting is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

        return MeetingSummarizeResponse(
            meeting_id=updated_meeting.meeting_id,
            status=updated_meeting.status,
            summary_text=updated_meeting.summary_text,
        )


meeting_service = MeetingService()
