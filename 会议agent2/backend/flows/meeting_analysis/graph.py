"""以最终总结节点结束的会议分析图。"""

from langgraph.graph import END, START, StateGraph

from backend.flows.meeting_analysis.nodes import (
    aggregate,
    content_agent,
    prepare,
    rag_decider_agent,
    risk_agent,
    summary_agent,
    task_agent,
)
from backend.flows.meeting_analysis.state import MeetingAnalysisState


def build_meeting_analysis_graph():
    """构建带总结生成能力的会议分析图。"""
    graph_builder = StateGraph(MeetingAnalysisState)
    graph_builder.add_node("prepare", prepare)
    graph_builder.add_node("content_agent", content_agent)
    graph_builder.add_node("task_agent", task_agent)
    graph_builder.add_node("risk_agent", risk_agent)
    graph_builder.add_node("aggregate", aggregate)
    graph_builder.add_node("rag_decider_agent", rag_decider_agent)
    graph_builder.add_node("summary_agent", summary_agent)

    graph_builder.add_edge(START, "prepare")
    graph_builder.add_edge("prepare", "content_agent")
    graph_builder.add_edge("prepare", "task_agent")
    graph_builder.add_edge("prepare", "risk_agent")

    graph_builder.add_edge("content_agent", "aggregate")
    graph_builder.add_edge("task_agent", "aggregate")
    graph_builder.add_edge("risk_agent", "aggregate")

    graph_builder.add_edge("aggregate", "rag_decider_agent")
    graph_builder.add_edge("rag_decider_agent", "summary_agent")
    graph_builder.add_edge("summary_agent", END)

    return graph_builder.compile()


meeting_analysis_graph = build_meeting_analysis_graph()
