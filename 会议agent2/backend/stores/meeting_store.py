from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import psycopg

from backend.core.config import load_postgres_config


@dataclass(slots=True)
class MeetingRow:
    """由 meetings 表映射而来的数据库记录。"""

    meeting_id: str
    title: str
    meeting_category: str
    audio_file_name: str
    stored_file_path: str
    oss_object_key: str
    transcript_text: str
    summary_text: str
    error_message: str
    status: str
    created_at: datetime
    updated_at: datetime


class MeetingStore:
    """会议任务记录的持久化层。"""

    def __init__(self) -> None:
        raw_config = load_postgres_config()
        self.hosts = raw_config.get("hosts", [])
        if not self.hosts and raw_config.get("host"):
            self.hosts = [raw_config["host"]]
        self.port = int(raw_config["port"])
        self.database = raw_config["database"]
        self.user = raw_config["user"]
        self.password = raw_config["password"]

    def _build_dsn(self, host: str) -> str:
        return (
            f"host={host} port={self.port} dbname={self.database} "
            f"user={self.user} password={self.password}"
        )

    def _connect(self):
        """打开 PostgreSQL 连接。"""
        last_error = None
        for host in self.hosts:
            try:
                return psycopg.connect(self._build_dsn(host))
            except psycopg.OperationalError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise ValueError("No PostgreSQL hosts configured")

    def create_meeting(
        self,
        meeting_id: str,
        title: str,
        meeting_category: str,
        audio_file_name: str,
        stored_file_path: str,
        oss_object_key: str,
    ) -> MeetingRow:
        """插入一条新的会议任务记录。"""
        created_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO meetings (
                        meeting_id, title, meeting_category, audio_file_name, stored_file_path, oss_object_key,
                        transcript_text, summary_text, error_message, status, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, '', '', '', 'uploaded', %s, %s)
                    """,
                    (
                        meeting_id,
                        title,
                        meeting_category,
                        audio_file_name,
                        stored_file_path,
                        oss_object_key,
                        created_at,
                        created_at,
                    ),
                )
            connection.commit()
        return MeetingRow(
            meeting_id=meeting_id,
            title=title,
            meeting_category=meeting_category,
            audio_file_name=audio_file_name,
            stored_file_path=stored_file_path,
            oss_object_key=oss_object_key,
            transcript_text="",
            summary_text="",
            error_message="",
            status="uploaded",
            created_at=created_at,
            updated_at=created_at,
        )

    def get_meeting(self, meeting_id: str) -> MeetingRow | None:
        """根据 ID 读取单个会议任务。"""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT meeting_id, title, meeting_category, audio_file_name, stored_file_path, oss_object_key,
                           transcript_text, summary_text, error_message, status, created_at, updated_at
                    FROM meetings WHERE meeting_id = %s
                    """,
                    (meeting_id,),
                )
                row = cursor.fetchone()
        if row is None:
            return None
        return self._build_meeting_row(row)

    def update_transcription_result(
        self,
        meeting_id: str,
        transcript_text: str,
        status: str,
        error_message: str = "",
    ) -> MeetingRow | None:
        """更新单个会议任务的转写结果。"""
        updated_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE meetings
                    SET transcript_text = %s, error_message = %s, status = %s, updated_at = %s
                    WHERE meeting_id = %s
                    RETURNING meeting_id, title, meeting_category, audio_file_name, stored_file_path, oss_object_key,
                              transcript_text, summary_text, error_message, status, created_at, updated_at
                    """,
                    (transcript_text, error_message, status, updated_at, meeting_id),
                )
                row = cursor.fetchone()
            connection.commit()
        return None if row is None else self._build_meeting_row(row)

    def update_summary_result(self, meeting_id: str, summary_text: str) -> MeetingRow | None:
        """保存单个会议任务生成的总结。"""
        updated_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE meetings
                    SET summary_text = %s, updated_at = %s
                    WHERE meeting_id = %s
                    RETURNING meeting_id, title, meeting_category, audio_file_name, stored_file_path, oss_object_key,
                              transcript_text, summary_text, error_message, status, created_at, updated_at
                    """,
                    (summary_text, updated_at, meeting_id),
                )
                row = cursor.fetchone()
            connection.commit()
        return None if row is None else self._build_meeting_row(row)

    def get_recent_summaries_by_category(
        self,
        meeting_category: str,
        current_meeting_id: str,
        limit: int = 2,
    ) -> list[str]:
        """返回同一会议分类下最近的非空总结。"""
        normalized_category = meeting_category.strip()
        if not normalized_category:
            return []

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT summary_text
                    FROM meetings
                    WHERE meeting_category = %s
                      AND meeting_id <> %s
                      AND summary_text <> ''
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (normalized_category, current_meeting_id, limit),
                )
                rows = cursor.fetchall()
        return [str(row[0]).strip() for row in rows if row and str(row[0]).strip()]

    def _build_meeting_row(self, row) -> MeetingRow:
        """将数据库元组转换为 MeetingRow。"""
        return MeetingRow(
            meeting_id=row[0],
            title=row[1],
            meeting_category=row[2],
            audio_file_name=row[3],
            stored_file_path=row[4],
            oss_object_key=row[5],
            transcript_text=row[6],
            summary_text=row[7],
            error_message=row[8],
            status=row[9],
            created_at=row[10],
            updated_at=row[11],
        )
