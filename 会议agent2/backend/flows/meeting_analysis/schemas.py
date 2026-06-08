"""Structured output schemas for meeting analysis nodes."""

from typing import Literal

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """One extracted action item."""

    task: str = Field(default="")
    owner: str = Field(default="")
    deadline: str = Field(default="")


class ContentAnalysisResult(BaseModel):
    """Structured content extraction result."""

    meeting_topic: str = Field(default="")
    summary: str = Field(default="")
    key_points: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)


class TaskAnalysisResult(BaseModel):
    """Structured task extraction result."""

    action_items: list[ActionItem] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class RiskAnalysisResult(BaseModel):
    """Structured risk extraction result."""

    risks: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class RagDecisionResult(BaseModel):
    """Structured output for the RAG decision node."""

    needs_rag: bool = Field(default=False)
    rag_queries: list[str] = Field(default_factory=list)
    rag_context: str = Field(default="")


class SummaryResult(BaseModel):
    """Structured output for the final summary node."""

    summary_text: str = Field(default="")
