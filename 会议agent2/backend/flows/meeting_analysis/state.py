"""会议分析工作流的状态定义。"""

from typing import Any, TypedDict


class MeetingAnalysisState(TypedDict, total=False):
    """在会议分析节点之间传递的共享状态。"""

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
