"""API 输入输出模型。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


MeetingStatus = Literal["uploaded", "processing_asr", "processing_summary", "done", "failed"]


class MeetingUploadResponse(BaseModel):
    """会议上传响应。"""

    meeting_id: str = Field(..., description="会议任务 ID")
    title: str = Field(..., description="会议标题")
    status: MeetingStatus = Field(..., description="任务状态")
    original_file_name: str = Field(..., description="原始文件名")
    stored_file_path: str = Field(..., description="落盘文件路径")
    converted_file_path: str = Field(..., description="转码后文件路径")
    created_at: datetime = Field(..., description="创建时间")


class MeetingConvertResponse(BaseModel):
    """会议转码响应。"""

    meeting_id: str = Field(..., description="会议任务 ID")
    status: MeetingStatus = Field(..., description="任务状态")
    converted_file_path: str = Field(..., description="转码后文件路径")


class MeetingTranscribeResponse(BaseModel):
    """会议转写响应。"""

    meeting_id: str = Field(..., description="会议任务 ID")
    status: MeetingStatus = Field(..., description="任务状态")
    transcript_text: str = Field(..., description="转写文本")


class MeetingSummarizeResponse(BaseModel):
    """会议总结响应。"""

    meeting_id: str = Field(..., description="会议任务 ID")
    status: MeetingStatus = Field(..., description="任务状态")
    summary_text: str = Field(..., description="会议纪要")


class MeetingDetail(BaseModel):
    """会议详情响应。"""

    meeting_id: str = Field(..., description="会议任务 ID")
    title: str = Field(..., description="会议标题")
    organizer: str = Field(..., description="组织人")
    audio_file_name: str = Field(..., description="音频文件名")
    stored_file_path: str = Field(..., description="落盘文件路径")
    converted_file_path: str = Field(..., description="转码后文件路径")
    transcript_text: str = Field(..., description="转写文本")
    summary_text: str = Field(..., description="会议纪要")
    error_message: str = Field(..., description="错误信息")
    status: MeetingStatus = Field(..., description="任务状态")
    created_at: datetime = Field(..., description="创建时间")
