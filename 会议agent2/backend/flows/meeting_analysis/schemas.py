"""会议分析节点的结构化输出模型。"""

from typing import Literal

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """单个提取出的行动项。"""

    task: str = Field(default="")
    owner: str = Field(default="")
    deadline: str = Field(default="")


class ContentAnalysisResult(BaseModel):
    """结构化内容提取结果。"""

    meeting_topic: str = Field(default="")
    summary: str = Field(default="")
    key_points: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)


class TaskAnalysisResult(BaseModel):
    """结构化任务提取结果。"""

    action_items: list[ActionItem] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class RiskAnalysisResult(BaseModel):
    """结构化风险提取结果。"""

    risks: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class RagDecisionResult(BaseModel):
    """RAG 决策节点的结构化输出。"""

    needs_rag: bool = Field(default=False)
    rag_queries: list[str] = Field(default_factory=list)
    rag_context: str = Field(default="")


class SummaryResult(BaseModel):
    """最终总结节点的结构化输出。"""

    summary_text: str = Field(default="")
