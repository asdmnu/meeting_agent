"""Node implementations for the meeting analysis workflow."""

import json
from functools import lru_cache

from langchain.agents import create_agent

from backend.core.config import (
    load_content_prompt,
    load_rag_decider_prompt,
    load_risk_prompt,
    load_summary_prompt,
    load_task_prompt,
)
from backend.flows.meeting_analysis.schemas import (
    ContentAnalysisResult,
    RagDecisionResult,
    RiskAnalysisResult,
    SummaryResult,
    TaskAnalysisResult,
)
from backend.flows.meeting_analysis.state import MeetingAnalysisState
from backend.models.factory import get_chat_model
from backend.tools import search_meeting_knowledge


def prepare(state: MeetingAnalysisState) -> MeetingAnalysisState:
    """Initialize graph state from the input transcript."""
    meeting_id = str(state.get("meeting_id", "")).strip()
    meeting_category = str(state.get("meeting_category", "")).strip()
    transcript_text = str(state.get("transcript_text", "")).strip()
    history_context = str(state.get("history_context", "")).strip()

    return {
        "meeting_id": meeting_id,
        "meeting_category": meeting_category,
        "transcript_text": transcript_text,
        "history_context": history_context,
        "content_result": {},
        "task_result": {},
        "risk_result": {},
        "merged_result": {},
        "needs_rag": False,
        "rag_queries": [],
        "rag_context": "",
        "summary_text": "",
        "error_message": "",
    }


def content_agent(state: MeetingAnalysisState) -> MeetingAnalysisState:
    """Extract the main meeting content into a structured result."""
    transcript_text = str(state.get("transcript_text", "")).strip()
    prompt_template = load_content_prompt()
    prompt = prompt_template.format(transcript_text=transcript_text)

    model = get_chat_model().with_structured_output(ContentAnalysisResult)
    result = model.invoke(prompt)

    return {
        "content_result": result.model_dump(),
    }


def task_agent(state: MeetingAnalysisState) -> MeetingAnalysisState:
    """Extract action items and next steps into a structured result."""
    transcript_text = str(state.get("transcript_text", "")).strip()
    prompt_template = load_task_prompt()
    prompt = prompt_template.format(transcript_text=transcript_text)

    model = get_chat_model().with_structured_output(TaskAnalysisResult)
    result = model.invoke(prompt)

    return {
        "task_result": result.model_dump(),
    }


def risk_agent(state: MeetingAnalysisState) -> MeetingAnalysisState:
    """Extract risks, blockers, and open questions into a structured result."""
    transcript_text = str(state.get("transcript_text", "")).strip()
    prompt_template = load_risk_prompt()
    prompt = prompt_template.format(transcript_text=transcript_text)

    model = get_chat_model().with_structured_output(RiskAnalysisResult)
    result = model.invoke(prompt)

    return {
        "risk_result": result.model_dump(),
    }


def aggregate(state: MeetingAnalysisState) -> MeetingAnalysisState:
    """Merge the three parallel analysis outputs into one aggregated object."""
    merged_result = {
        "content_result": state.get("content_result", {}),
        "task_result": state.get("task_result", {}),
        "risk_result": state.get("risk_result", {}),
    }
    return {
        "merged_result": merged_result,
    }


@lru_cache(maxsize=1)
def build_rag_agent():
    """Build the shared RAG create-agent instance."""
    return create_agent(
        model=get_chat_model(),
        tools=[search_meeting_knowledge],
        system_prompt=load_rag_decider_prompt(),
        response_format=RagDecisionResult,
        name="meeting_rag_agent",
    )


def rag_decider_agent(state: MeetingAnalysisState) -> MeetingAnalysisState:
    """Run the real RAG agent with retrieval tool access."""
    prompt = load_rag_decider_prompt().format(
        content_result=json.dumps(state.get("content_result", {}), ensure_ascii=False, indent=2),
        task_result=json.dumps(state.get("task_result", {}), ensure_ascii=False, indent=2),
        risk_result=json.dumps(state.get("risk_result", {}), ensure_ascii=False, indent=2),
    )

    agent = build_rag_agent()
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        }
    )
    parsed = result["structured_response"]

    return {
        "needs_rag": parsed.needs_rag,
        "rag_queries": parsed.rag_queries,
        "rag_context": parsed.rag_context,
    }


def summary_agent(state: MeetingAnalysisState) -> MeetingAnalysisState:
    """Generate the final meeting summary from analysis outputs and RAG context."""
    prompt = load_summary_prompt().format(
        content_result=json.dumps(state.get("content_result", {}), ensure_ascii=False, indent=2),
        task_result=json.dumps(state.get("task_result", {}), ensure_ascii=False, indent=2),
        risk_result=json.dumps(state.get("risk_result", {}), ensure_ascii=False, indent=2),
        rag_context=str(state.get("rag_context", "")).strip(),
        history_context=str(state.get("history_context", "")).strip(),
    )

    model = get_chat_model().with_structured_output(SummaryResult)
    result = model.invoke(prompt)
    return {
        "summary_text": result.summary_text.strip(),
    }
