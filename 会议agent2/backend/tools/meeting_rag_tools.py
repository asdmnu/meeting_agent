"""RAG tool definitions for later LangChain agent integration."""

from __future__ import annotations

from langchain_core.tools import tool

from backend.stores.retrieval_store import retrieval_store


@tool
def search_meeting_knowledge(query: str) -> list[dict[str, str]]:
    """Search the meeting knowledge base for related background information."""
    return retrieval_store.search(query=query)

