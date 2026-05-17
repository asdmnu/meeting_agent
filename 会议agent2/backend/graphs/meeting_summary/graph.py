"""Meeting summary workflow graph definition."""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from backend.graphs.meeting_summary.nodes import (
    clean_transcript,
    extract_summary,
    finalize_summary,
    prepare_summary,
    render_summary,
    repair_summary,
    validate_summary,
)
from backend.graphs.meeting_summary.state import MeetingSummaryState


def route_after_validation(state: MeetingSummaryState) -> str:
    validation_result = state.get("validation_result", {})
    if validation_result.get("passed"):
        return "render"
    if state.get("retry_count", 0) < state.get("max_retries", 1):
        return "repair"
    return "finalize"


def build_meeting_summary_graph():
    graph_builder = StateGraph(MeetingSummaryState)
    checkpointer = InMemorySaver()

    graph_builder.add_node("prepare_summary", prepare_summary)
    graph_builder.add_node("clean_transcript", clean_transcript)
    graph_builder.add_node("extract_summary", extract_summary)
    graph_builder.add_node("validate_summary", validate_summary)
    graph_builder.add_node("repair_summary", repair_summary)
    graph_builder.add_node("render_summary", render_summary)
    graph_builder.add_node("finalize_summary", finalize_summary)

    graph_builder.add_edge(START, "prepare_summary")
    graph_builder.add_edge("prepare_summary", "clean_transcript")
    graph_builder.add_edge("clean_transcript", "extract_summary")
    graph_builder.add_edge("extract_summary", "validate_summary")
    graph_builder.add_conditional_edges(
        "validate_summary",
        route_after_validation,
        {
            "render": "render_summary",
            "repair": "repair_summary",
            "finalize": "finalize_summary",
        },
    )
    graph_builder.add_edge("repair_summary", "validate_summary")
    graph_builder.add_edge("render_summary", "finalize_summary")
    graph_builder.add_edge("finalize_summary", END)

    return graph_builder.compile(checkpointer=checkpointer)


meeting_summary_graph = build_meeting_summary_graph()
