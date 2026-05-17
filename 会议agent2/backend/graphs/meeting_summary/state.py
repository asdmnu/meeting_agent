"""Meeting summary workflow state definition."""

from typing import Any, TypedDict


class MeetingSummaryState(TypedDict, total=False):
    meeting_id: str
    transcript_text: str
    clean_transcript_text: str
    summary_json: dict[str, Any]
    summary_text: str
    validation_result: dict[str, Any]
    recent_meetings_memory: list[dict[str, Any]]
    recent_meetings_context: str
    current_meeting_memory: dict[str, Any]
    retry_count: int
    max_retries: int
    summary_stage: str
    needs_human_review: bool
    error_message: str
