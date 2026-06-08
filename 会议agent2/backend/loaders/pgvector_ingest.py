"""加载 .txt 知识文件，切分后写入 pgvector。"""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.core.config import load_rag_config
from backend.core.paths import get_abs_path
from backend.stores.pgvector_store import PGVectorStore


RAG_CONFIG = load_rag_config()
DATA_DIR = Path(get_abs_path("data/knowledge"))


def load_source_documents() -> list[Document]:
    """从 data/knowledge 读取受支持的知识文件。"""
    documents: list[Document] = []
    allow_types = {item.lower().lstrip(".") for item in RAG_CONFIG["allow_knowledge_file_type"]}

    if not DATA_DIR.exists():
        return []

    for file_path in sorted(DATA_DIR.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower().lstrip(".") not in allow_types:
            continue

        relative_path = file_path.relative_to(DATA_DIR)
        category = relative_path.parts[0] if len(relative_path.parts) > 1 else "default"
        content = file_path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": file_path.name,
                    "path": str(relative_path).replace("\\", "/"),
                    "category": category,
                },
            )
        )
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    """按照 rag.yml 配置切分文档。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(RAG_CONFIG["chunk_size"]),
        chunk_overlap=int(RAG_CONFIG["chunk_overlap"]),
        separators=RAG_CONFIG["separators"],
    )

    chunks: list[Document] = []
    for document in documents:
        split_docs = splitter.split_documents([document])
        for chunk_index, chunk in enumerate(split_docs):
            chunk.metadata["chunk_index"] = chunk_index
            chunks.append(chunk)
    return chunks


def ingest_documents(chunks: list[Document], vector_store: PGVectorStore) -> None:
    """将文本分块写入 pgvector 数据表。"""
    if not chunks:
        print("No knowledge chunks to ingest.")
        return
    vector_store.add_documents(chunks)


def main() -> None:
    vector_store = PGVectorStore()
    documents = load_source_documents()
    chunks = split_documents(documents)
    ingest_documents(chunks, vector_store)

    print(f"Scanned knowledge documents: {len(documents)}")
    print(f"Generated chunks: {len(chunks)}")
    print(f"PostgreSQL table: {vector_store.config.table_name}")


if __name__ == "__main__":
    main()
