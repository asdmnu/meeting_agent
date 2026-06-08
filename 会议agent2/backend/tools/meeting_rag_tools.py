"""供后续 LangChain 智能体集成使用的 RAG 工具定义。"""

from __future__ import annotations

from langchain_core.tools import tool

from backend.stores.retrieval_store import retrieval_store


@tool
def search_meeting_knowledge(query: str) -> list[dict[str, str]]:
    """在会议知识库中搜索相关背景信息。"""
    return retrieval_store.search(query=query)
