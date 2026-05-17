from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


MeetingStatus = Literal["uploaded", "processing_asr", "processing_summary", "review_required", "done", "failed"]


class MeetingUploadResponse(BaseModel):
    meeting_id: str = Field(...)
    title: str = Field(...)
    status: MeetingStatus = Field(...)
    original_file_name: str = Field(...)
    stored_file_path: str = Field(...)
    created_at: datetime = Field(...)


class MeetingTranscribeResponse(BaseModel):
    meeting_id: str = Field(...)
    status: MeetingStatus = Field(...)
    transcript_text: str = Field(...)


class MeetingSummarizeResponse(BaseModel):
    meeting_id: str = Field(...)
    status: MeetingStatus = Field(...)
    clean_transcript_text: str = Field(...)
    summary_json: dict = Field(...)
    summary_text: str = Field(...)
    summary_stage: str = Field(...)
    summary_check_json: dict = Field(...)
    summary_retry_count: int = Field(...)
    needs_human_review: bool = Field(...)


class MeetingDetail(BaseModel):
    meeting_id: str = Field(...)
    title: str = Field(...)
    organizer: str = Field(...)
    audio_file_name: str = Field(...)
    stored_file_path: str = Field(...)
    oss_object_key: str = Field(...)
    transcript_text: str = Field(...)
    clean_transcript_text: str = Field(...)
    summary_json: dict = Field(...)
    summary_text: str = Field(...)
    summary_stage: str = Field(...)
    summary_check_json: dict = Field(...)
    summary_retry_count: int = Field(...)
    needs_human_review: bool = Field(...)
    error_message: str = Field(...)
    status: MeetingStatus = Field(...)
    created_at: datetime = Field(...)
