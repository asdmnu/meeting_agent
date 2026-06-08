"""在 pgvector 知识库仍为空时完成初始化。"""

from backend.loaders.pgvector_ingest import ingest_documents, load_source_documents, split_documents
from backend.stores.pgvector_store import PGVectorStore


def main() -> None:
    vector_store = PGVectorStore()
    if vector_store.has_documents():
        print("Knowledge base already initialized.")
        return

    documents = load_source_documents()
    if not documents:
        print("No knowledge files found under data/knowledge, skip initialization.")
        return

    chunks = split_documents(documents)
    ingest_documents(chunks, vector_store)
    print(f"Initialized knowledge base with {len(documents)} documents and {len(chunks)} chunks.")


if __name__ == "__main__":
    main()
