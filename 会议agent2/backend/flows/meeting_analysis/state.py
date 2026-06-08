"""State definitions for the meeting analysis workflow."""

from typing import Any, TypedDict


class MeetingAnalysisState(TypedDict, total=False):
    """Shared state passed between meeting analysis nodes."""

    meeting_id: str
    meeting_category: str
    transcript_text: str
    history_context: str

    content_result: dict[str, Any]
    task_result: dict[str, Any]
    risk_result: dict[str, Any]

    merged_result: dict[str, Any]
    needs_rag: bool
    rag_queries: list[str]
    rag_context: str
    summary_text: str
    error_message: str
