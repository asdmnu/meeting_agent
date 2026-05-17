"""Meeting summary workflow nodes."""

from datetime import datetime

from backend.graphs.meeting_summary.state import MeetingSummaryState
from backend.services.summary_service import summary_service
from backend.services.summary_validator import summary_validator_service


MEMORY_LIMIT = 5


def _normalize_recent_meetings_memory(memory_items: list[dict] | None) -> list[dict]:
    if not isinstance(memory_items, list):
        return []
    normalized_items: list[dict] = []
    for item in memory_items:
        if not isinstance(item, dict):
            continue
        normalized_items.append(
            {
                "meeting_id": str(item.get("meeting_id", "")).strip(),
                "meeting_topic": str(item.get("meeting_topic", "")).strip(),
                "meeting_time": str(item.get("meeting_time", "")).strip(),
                "keywords": [str(keyword).strip() for keyword in item.get("keywords", []) if str(keyword).strip()],
                "decisions": [str(decision).strip() for decision in item.get("decisions", []) if str(decision).strip()],
                "action_items_summary": [
                    str(action).strip() for action in item.get("action_items_summary", []) if str(action).strip()
                ],
                "risks": [str(risk).strip() for risk in item.get("risks", []) if str(risk).strip()],
                "review_required": bool(item.get("review_required", False)),
            }
        )
    return normalized_items[:MEMORY_LIMIT]


def _format_recent_meetings_context(memory_items: list[dict]) -> str:
    if not memory_items:
        return "无"

    lines: list[str] = []
    for index, item in enumerate(memory_items, start=1):
        lines.append(f"历史会议 {index}:")
        lines.append(f"- meeting_id: {item.get('meeting_id', '') or 'unknown'}")
        lines.append(f"- topic: {item.get('meeting_topic', '') or 'unknown'}")
        lines.append(f"- time: {item.get('meeting_time', '') or 'unknown'}")
        lines.append(f"- keywords: {', '.join(item.get('keywords', [])) or '无'}")
        lines.append(f"- decisions: {'；'.join(item.get('decisions', [])) or '无'}")
        lines.append(f"- action_items: {'；'.join(item.get('action_items_summary', [])) or '无'}")
        lines.append(f"- risks: {'；'.join(item.get('risks', [])) or '无'}")
        lines.append(f"- review_required: {item.get('review_required', False)}")
    return "\n".join(lines)


def _build_current_meeting_memory(state: MeetingSummaryState) -> dict:
    summary_json = state.get("summary_json", {})
    action_items = summary_json.get("action_items", [])
    action_items_summary = []
    if isinstance(action_items, list):
        for item in action_items:
            if not isinstance(item, dict):
                continue
            task = str(item.get("task", "")).strip()
            owner = str(item.get("owner", "")).strip()
            if not task:
                continue
            action_items_summary.append(f"{task}（负责人：{owner or '待定'}）")

    keywords = []
    for value in [
        summary_json.get("meeting_topic", ""),
        *summary_json.get("key_points", []),
        *summary_json.get("decisions", []),
    ]:
        text = str(value).strip()
        if text:
            keywords.append(text[:40])

    deduped_keywords = list(dict.fromkeys(keywords))[:8]

    return {
        "meeting_id": str(state.get("meeting_id", "")).strip(),
        "meeting_topic": str(summary_json.get("meeting_topic", "")).strip(),
        "meeting_time": datetime.utcnow().isoformat() + "Z",
        "keywords": deduped_keywords,
        "decisions": [str(item).strip() for item in summary_json.get("decisions", []) if str(item).strip()][:5],
        "action_items_summary": action_items_summary[:5],
        "risks": [str(item).strip() for item in summary_json.get("risks", []) if str(item).strip()][:5],
        "review_required": bool(state.get("needs_human_review", False)),
    }


def prepare_summary(state: MeetingSummaryState) -> MeetingSummaryState:
    recent_meetings_memory = _normalize_recent_meetings_memory(state.get("recent_meetings_memory", []))
    return {
        "summary_stage": "prepare",
        "clean_transcript_text": "",
        "summary_json": {},
        "summary_text": "",
        "validation_result": {},
        "recent_meetings_memory": recent_meetings_memory,
        "recent_meetings_context": _format_recent_meetings_context(recent_meetings_memory),
        "current_meeting_memory": {},
        "retry_count": state.get("retry_count", 0),
        "needs_human_review": False,
        "error_message": "",
    }


def clean_transcript(state: MeetingSummaryState) -> MeetingSummaryState:
    return {
        "summary_stage": "clean",
        "clean_transcript_text": summary_service.clean_transcript(state.get("transcript_text", "")),
    }


def extract_summary(state: MeetingSummaryState) -> MeetingSummaryState:
    return {
        "summary_stage": "extract",
        "summary_json": summary_service.extract_summary(
            state.get("clean_transcript_text", ""),
            state.get("recent_meetings_context", "无"),
        ),
    }


def validate_summary(state: MeetingSummaryState) -> MeetingSummaryState:
    return {
        "summary_stage": "validate",
        "validation_result": summary_validator_service.validate_summary(
            state.get("clean_transcript_text", ""),
            state.get("summary_json", {}),
            state.get("recent_meetings_context", "无"),
        ),
    }


def repair_summary(state: MeetingSummaryState) -> MeetingSummaryState:
    return {
        "summary_stage": "repair",
        "retry_count": state.get("retry_count", 0) + 1,
        "summary_json": summary_service.repair_summary(
            state.get("clean_transcript_text", ""),
            state.get("summary_json", {}),
            state.get("validation_result", {}),
        ),
    }


def render_summary(state: MeetingSummaryState) -> MeetingSummaryState:
    return {
        "summary_stage": "render",
        "summary_text": summary_service.render_summary(state.get("summary_json", {})),
    }


def finalize_summary(state: MeetingSummaryState) -> MeetingSummaryState:
    validation_passed = bool(state.get("validation_result", {}).get("passed"))
    summary_text = str(state.get("summary_text", "")).strip()
    recent_meetings_memory = _normalize_recent_meetings_memory(state.get("recent_meetings_memory", []))
    current_meeting_memory = {}

    if state.get("summary_json"):
        current_meeting_memory = _build_current_meeting_memory(state)
        meeting_id = current_meeting_memory.get("meeting_id", "")
        filtered_memory = [
            item for item in recent_meetings_memory if item.get("meeting_id", "") != meeting_id
        ]
        recent_meetings_memory = [current_meeting_memory, *filtered_memory][:MEMORY_LIMIT]

    if validation_passed and summary_text:
        return {
            "summary_stage": "done",
            "needs_human_review": False,
            "current_meeting_memory": current_meeting_memory,
            "recent_meetings_memory": recent_meetings_memory,
            "recent_meetings_context": _format_recent_meetings_context(recent_meetings_memory),
        }
    return {
        "summary_stage": "review_required",
        "needs_human_review": True,
        "current_meeting_memory": current_meeting_memory,
        "recent_meetings_memory": recent_meetings_memory,
        "recent_meetings_context": _format_recent_meetings_context(recent_meetings_memory),
    }
