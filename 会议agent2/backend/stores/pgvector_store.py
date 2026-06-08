"""Minimal PostgreSQL + pgvector store for knowledge ingestion and retrieval."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import psycopg
from langchain_core.documents import Document

from backend.core.config import load_postgres_config
from backend.models.factory import get_embedding_model


DISTANCE_OPERATORS = {
    "cosine": "<=>",
    "l2": "<->",
    "inner_product": "<#>",
}


@dataclass(slots=True)
class PostgresConfig:
    hosts: list[str]
    port: int
    database: str
    user: str
    password: str
    table_name: str
    embedding_dimension: int
    distance_strategy: str = "cosine"
    fts_regconfig: str = "simple"
    vector_search_k: int = 8
    keyword_search_k: int = 8
    hybrid_top_k: int = 3
    rrf_k: int = 60


@dataclass(slots=True)
class SearchHit:
    content: str
    metadata: dict[str, Any]
    vector_rank: int | None = None
    keyword_rank: int | None = None
    vector_score: float | None = None
    keyword_score: float | None = None
    fusion_score: float = 0.0


class PGVectorStore:
    """Minimal pgvector store for knowledge chunk ingestion and retrieval."""

    def __init__(self):
        raw_config = load_postgres_config()
        hosts = raw_config.get("hosts", [])
        if not hosts and raw_config.get("host"):
            hosts = [raw_config["host"]]
        self.config = PostgresConfig(
            hosts=hosts,
            port=int(raw_config["port"]),
            database=raw_config["database"],
            user=raw_config["user"],
            password=raw_config["password"],
            table_name=raw_config["table_name"],
            embedding_dimension=int(raw_config["embedding_dimension"]),
            distance_strategy=raw_config.get("distance_strategy", "cosine"),
            fts_regconfig=raw_config.get("fts_regconfig", "simple"),
            vector_search_k=int(raw_config.get("vector_search_k", 8)),
            keyword_search_k=int(raw_config.get("keyword_search_k", 8)),
            hybrid_top_k=int(raw_config.get("hybrid_top_k", 3)),
            rrf_k=int(raw_config.get("rrf_k", 60)),
        )
        self.embedding_model = get_embedding_model()
        self.distance_operator = DISTANCE_OPERATORS.get(
            self.config.distance_strategy,
            DISTANCE_OPERATORS["cosine"],
        )
        self._ensure_schema()

    @property
    def fts_regconfig(self) -> str:
        regconfig = self.config.fts_regconfig.strip()
        if not re.fullmatch(r"[A-Za-z0-9_]+", regconfig):
            return "simple"
        return regconfig or "simple"

    def _build_dsn(self, host: str) -> str:
        return (
            f"host={host} "
            f"port={self.config.port} "
            f"dbname={self.config.database} "
            f"user={self.config.user} "
            f"password={self.config.password}"
        )

    def _connect(self):
        last_error = None
        for host in self.config.hosts:
            try:
                return psycopg.connect(self._build_dsn(host))
            except psycopg.OperationalError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise ValueError("No PostgreSQL hosts configured")

    def _ensure_schema(self) -> None:
        table_name = self.config.table_name
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id BIGSERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        source TEXT NOT NULL,
                        path TEXT NOT NULL,
                        category TEXT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        embedding VECTOR({self.config.embedding_dimension}) NOT NULL,
                        search_vector TSVECTOR
                    )
                    """
                )
                cursor.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {table_name}_search_vector_idx
                    ON {table_name} USING GIN (search_vector)
                    """
                )
                cursor.execute(
                    f"""
                    UPDATE {table_name}
                    SET search_vector = to_tsvector('{self.fts_regconfig}', content)
                    WHERE search_vector IS NULL
                    """
                )
            connection.commit()

    def reset_collection(self) -> None:
        table_name = self.config.table_name
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            connection.commit()
        self._ensure_schema()

    def has_documents(self) -> bool:
        table_name = self.config.table_name
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT EXISTS (SELECT 1 FROM {table_name} LIMIT 1)")
                row = cursor.fetchone()
        return bool(row and row[0])

    def add_documents(self, chunks: list[Document]) -> None:
        if not chunks:
            return

        table_name = self.config.table_name
        texts = [chunk.page_content for chunk in chunks]
        embeddings = self.embedding_model.embed_documents(texts)

        rows: list[tuple[Any, ...]] = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            metadata = dict(chunk.metadata)
            rows.append(
                (
                    chunk.page_content,
                    str(metadata.get("source", "unknown")),
                    str(metadata.get("path", "")),
                    str(metadata.get("category", "default")),
                    int(metadata.get("chunk_index", 0)),
                    json.dumps(metadata, ensure_ascii=False),
                    self._vector_literal(embedding),
                    chunk.page_content,
                )
            )

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    f"""
                    INSERT INTO {table_name} (
                        content,
                        source,
                        path,
                        category,
                        chunk_index,
                        metadata,
                        embedding,
                        search_vector
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s::jsonb,
                        %s::vector,
                        to_tsvector('{self.fts_regconfig}', %s)
                    )
                    """,
                    rows,
                )
            connection.commit()

    def vector_search(self, query: str, k: int | None = None) -> list[SearchHit]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        query_embedding = self.embedding_model.embed_query(normalized_query)
        vector_literal = self._vector_literal(query_embedding)
        top_k = k or self.config.vector_search_k
        table_name = self.config.table_name

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT
                        content,
                        source,
                        path,
                        category,
                        chunk_index,
                        metadata,
                        embedding {self.distance_operator} %s::vector AS vector_distance
                    FROM {table_name}
                    ORDER BY vector_distance
                    LIMIT %s
                    """,
                    (vector_literal, top_k),
                )
                rows = cursor.fetchall()

        hits: list[SearchHit] = []
        for rank, row in enumerate(rows, start=1):
            content, source, path, category, chunk_index, metadata, vector_distance = row
            hits.append(
                SearchHit(
                    content=content,
                    metadata=self._merge_metadata(source, path, category, chunk_index, metadata),
                    vector_rank=rank,
                    vector_score=float(vector_distance),
                )
            )
        return hits

    def keyword_search(self, query: str, k: int | None = None) -> list[SearchHit]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        top_k = k or self.config.keyword_search_k
        table_name = self.config.table_name

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT
                        content,
                        source,
                        path,
                        category,
                        chunk_index,
                        metadata,
                        ts_rank_cd(
                            search_vector,
                            plainto_tsquery('{self.fts_regconfig}', %s)
                        ) AS keyword_score
                    FROM {table_name}
                    WHERE search_vector @@ plainto_tsquery('{self.fts_regconfig}', %s)
                    ORDER BY keyword_score DESC
                    LIMIT %s
                    """,
                    (normalized_query, normalized_query, top_k),
                )
                rows = cursor.fetchall()

        if not rows:
            return self._fallback_keyword_search(normalized_query, top_k)

        hits: list[SearchHit] = []
        for rank, row in enumerate(rows, start=1):
            content, source, path, category, chunk_index, metadata, keyword_score = row
            hits.append(
                SearchHit(
                    content=content,
                    metadata=self._merge_metadata(source, path, category, chunk_index, metadata),
                    keyword_rank=rank,
                    keyword_score=float(keyword_score),
                )
            )
        return hits

    def hybrid_search(self, query: str, k: int | None = None) -> list[Document]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        top_k = k or self.config.hybrid_top_k
        vector_hits = self.vector_search(normalized_query, k=self.config.vector_search_k)
        keyword_hits = self.keyword_search(normalized_query, k=self.config.keyword_search_k)

        if not keyword_hits:
            return self._hits_to_documents(vector_hits[:top_k])

        merged_hits: dict[tuple[str, str, str], SearchHit] = {}
        for hit in vector_hits:
            merged_hits[self._hit_key(hit)] = hit

        for hit in keyword_hits:
            key = self._hit_key(hit)
            existing = merged_hits.get(key)
            if existing is None:
                merged_hits[key] = hit
                continue
            existing.keyword_rank = hit.keyword_rank
            existing.keyword_score = hit.keyword_score

        ranked_hits = list(merged_hits.values())
        for hit in ranked_hits:
            hit.fusion_score = self._rrf_score(hit)
        ranked_hits.sort(
            key=lambda item: (
                item.fusion_score,
                -(item.keyword_score or 0.0),
                -((1.0 / (1.0 + item.vector_score)) if item.vector_score is not None else 0.0),
            ),
            reverse=True,
        )
        return self._hits_to_documents(ranked_hits[:top_k])

    @staticmethod
    def _vector_literal(embedding: list[float]) -> str:
        return "[" + ",".join(str(value) for value in embedding) + "]"

    @staticmethod
    def _merge_metadata(
        source: str,
        path: str,
        category: str,
        chunk_index: int,
        metadata: dict[str, Any] | Any,
    ) -> dict[str, Any]:
        combined_metadata = {
            "source": source,
            "path": path,
            "category": category,
            "chunk_index": chunk_index,
        }
        if isinstance(metadata, dict):
            combined_metadata.update(metadata)
        return combined_metadata

    @staticmethod
    def _hit_key(hit: SearchHit) -> tuple[str, str, str]:
        return (
            str(hit.metadata.get("path", "")),
            str(hit.metadata.get("chunk_index", "")),
            hit.content,
        )

    def _rrf_score(self, hit: SearchHit) -> float:
        score = 0.0
        if hit.vector_rank is not None:
            score += 1.0 / (self.config.rrf_k + hit.vector_rank)
        if hit.keyword_rank is not None:
            score += 1.0 / (self.config.rrf_k + hit.keyword_rank)
        return score

    def _fallback_keyword_search(self, query: str, k: int) -> list[SearchHit]:
        keywords = [item for item in re.split(r"\s+", query.strip()) if item]
        if not keywords:
            return []

        conditions = " OR ".join(["content ILIKE %s" for _ in keywords])
        score_terms = " + ".join([f"(CASE WHEN content ILIKE %s THEN 1 ELSE 0 END)" for _ in keywords])
        params: list[Any] = [f"%{keyword}%" for keyword in keywords]
        score_params: list[Any] = [f"%{keyword}%" for keyword in keywords]
        table_name = self.config.table_name

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT
                        content,
                        source,
                        path,
                        category,
                        chunk_index,
                        metadata,
                        ({score_terms}) AS keyword_score
                    FROM {table_name}
                    WHERE {conditions}
                    ORDER BY keyword_score DESC, chunk_index ASC
                    LIMIT %s
                    """,
                    tuple(score_params + params + [k]),
                )
                rows = cursor.fetchall()

        hits: list[SearchHit] = []
        for rank, row in enumerate(rows, start=1):
            content, source, path, category, chunk_index, metadata, keyword_score = row
            hits.append(
                SearchHit(
                    content=content,
                    metadata=self._merge_metadata(source, path, category, chunk_index, metadata),
                    keyword_rank=rank,
                    keyword_score=float(keyword_score),
                )
            )
        return hits

    @staticmethod
    def _hits_to_documents(hits: list[SearchHit]) -> list[Document]:
        return [Document(page_content=hit.content, metadata=hit.metadata) for hit in hits]
