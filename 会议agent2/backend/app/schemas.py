"""会议转写 API 的 Pydantic 模型。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


MeetingStatus = Literal["uploaded", "transcribed", "failed"]


class MeetingUploadResponse(BaseModel):
    """上传会议文件后返回的响应。"""

    meeting_id: str = Field(...)
    title: str = Field(...)
    meeting_category: str = Field(default="")
    status: MeetingStatus = Field(...)
    original_file_name: str = Field(...)
    created_at: datetime = Field(...)


class MeetingTranscribeResponse(BaseModel):
    """转写完成后返回的响应。"""

    meeting_id: str = Field(...)
    status: MeetingStatus = Field(...)
    transcript_text: str = Field(...)
    summary_text: str = Field(default="")


class MeetingDetail(BaseModel):
    """供查询页面使用的会议任务详细状态。"""

    meeting_id: str = Field(...)
    title: str = Field(...)
    meeting_category: str = Field(default="")
    audio_file_name: str = Field(...)
    transcript_text: str = Field(...)
    summary_text: str = Field(default="")
    error_message: str = Field(...)
    status: MeetingStatus = Field(...)
    created_at: datetime = Field(...)
