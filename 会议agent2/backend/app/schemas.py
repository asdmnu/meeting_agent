"""Pydantic schemas for the meeting transcription API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


MeetingStatus = Literal["uploaded", "transcribed", "failed"]


class MeetingUploadResponse(BaseModel):
    """Response returned after a meeting file is uploaded."""

    meeting_id: str = Field(...)
    title: str = Field(...)
    meeting_category: str = Field(default="")
    status: MeetingStatus = Field(...)
    original_file_name: str = Field(...)
    created_at: datetime = Field(...)


class MeetingTranscribeResponse(BaseModel):
    """Response returned after transcription finishes."""

    meeting_id: str = Field(...)
    status: MeetingStatus = Field(...)
    transcript_text: str = Field(...)
    summary_text: str = Field(default="")


class MeetingDetail(BaseModel):
    """Detailed meeting task state for query pages."""

    meeting_id: str = Field(...)
    title: str = Field(...)
    meeting_category: str = Field(default="")
    audio_file_name: str = Field(...)
    transcript_text: str = Field(...)
    summary_text: str = Field(default="")
    error_message: str = Field(...)
    status: MeetingStatus = Field(...)
    created_at: datetime = Field(...)
