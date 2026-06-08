"""会议项目的知识检索层。"""

from __future__ import annotations

from langchain_core.documents import Document

from backend.core.config import load_rag_config
from backend.stores.pgvector_store import PGVectorStore


RAG_CONFIG = load_rag_config()


class RetrievalStore:
    """封装 pgvector 搜索并规范化返回字段。"""

    def __init__(self):
        self.top_k = int(RAG_CONFIG["top_k"])
        self._vector_store: PGVectorStore | None = None

    @property
    def vector_store(self) -> PGVectorStore:
        if self._vector_store is None:
            self._vector_store = PGVectorStore()
        return self._vector_store

    def search(self, query: str, top_k: int | None = None) -> list[dict[str, str]]:
        """执行混合检索并返回轻量结果结构。"""
        documents = self.vector_store.hybrid_search(query, k=top_k or self.top_k)
        return [self._document_to_dict(document) for document in documents]

    @staticmethod
    def _document_to_dict(document: Document) -> dict[str, str]:
        return {
            "source": str(document.metadata.get("source", "unknown")),
            "content": document.page_content,
            "path": str(document.metadata.get("path", "")),
            "chunk_index": str(document.metadata.get("chunk_index", "")),
            "category": str(document.metadata.get("category", "")),
        }


retrieval_store = RetrievalStore()
