from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import psycopg

from backend.core.config import load_postgres_config


@dataclass(slots=True)
class PostgresConfig:
    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass(slots=True)
class MeetingRow:
    meeting_id: str
    title: str
    organizer: str
    audio_file_name: str
    stored_file_path: str
    converted_file_path: str
    transcript_text: str
    summary_text: str
    error_message: str
    status: str
    created_at: datetime
    updated_at: datetime


class MeetingStore:
    def __init__(self) -> None:
        raw_config = load_postgres_config()
        self.config = PostgresConfig(
            host=raw_config["host"],
            port=int(raw_config["port"]),
            database=raw_config["database"],
            user=raw_config["user"],
            password=raw_config["password"],
        )

    @property
    def dsn(self) -> str:
        return (
            f"host={self.config.host} "
            f"port={self.config.port} "
            f"dbname={self.config.database} "
            f"user={self.config.user} "
            f"password={self.config.password}"
        )

    def _connect(self):
        return psycopg.connect(self.dsn)

    def create_meeting(
        self,
        meeting_id: str,
        title: str,
        organizer: str,
        audio_file_name: str,
        stored_file_path: str,
        converted_file_path: str = "",
        transcript_text: str = "",
        summary_text: str = "",
        error_message: str = "",
        status: str = "uploaded",
    ) -> MeetingRow:
        created_at = datetime.now(timezone.utc)
        updated_at = created_at
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO meetings (
                        meeting_id,
                        title,
                        organizer,
                        audio_file_name,
                        stored_file_path,
                        converted_file_path,
                        transcript_text,
                        summary_text,
                        error_message,
                        status,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        meeting_id,
                        title,
                        organizer,
                        audio_file_name,
                        stored_file_path,
                        converted_file_path,
                        transcript_text,
                        summary_text,
                        error_message,
                        status,
                        created_at,
                        updated_at,
                    ),
                )
            connection.commit()
        return MeetingRow(
            meeting_id=meeting_id,
            title=title,
            organizer=organizer,
            audio_file_name=audio_file_name,
            stored_file_path=stored_file_path,
            converted_file_path=converted_file_path,
            transcript_text=transcript_text,
            summary_text=summary_text,
            error_message=error_message,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
        )

    def get_meeting(self, meeting_id: str) -> MeetingRow | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        meeting_id,
                        title,
                        organizer,
                        audio_file_name,
                        stored_file_path,
                        converted_file_path,
                        transcript_text,
                        summary_text,
                        error_message,
                        status,
                        created_at,
                        updated_at
                    FROM meetings
                    WHERE meeting_id = %s
                    """,
                    (meeting_id,),
                )
                row = cursor.fetchone()

        if row is None:
            return None

        return MeetingRow(
            meeting_id=row[0],
            title=row[1],
            organizer=row[2],
            audio_file_name=row[3],
            stored_file_path=row[4],
            converted_file_path=row[5],
            transcript_text=row[6],
            summary_text=row[7],
            error_message=row[8],
            status=row[9],
            created_at=row[10],
            updated_at=row[11],
        )

    def update_conversion_result(
        self,
        meeting_id: str,
        converted_file_path: str,
        status: str,
    ) -> MeetingRow | None:
        updated_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE meetings
                    SET converted_file_path = %s,
                        status = %s,
                        updated_at = %s
                    WHERE meeting_id = %s
                    RETURNING
                        meeting_id,
                        title,
                        organizer,
                        audio_file_name,
                        stored_file_path,
                        converted_file_path,
                        transcript_text,
                        summary_text,
                        error_message,
                        status,
                        created_at,
                        updated_at
                    """,
                    (
                        converted_file_path,
                        status,
                        updated_at,
                        meeting_id,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()

        if row is None:
            return None

        return MeetingRow(
            meeting_id=row[0],
            title=row[1],
            organizer=row[2],
            audio_file_name=row[3],
            stored_file_path=row[4],
            converted_file_path=row[5],
            transcript_text=row[6],
            summary_text=row[7],
            error_message=row[8],
            status=row[9],
            created_at=row[10],
            updated_at=row[11],
        )

    def update_transcription_result(
        self,
        meeting_id: str,
        transcript_text: str,
        status: str,
        error_message: str = "",
    ) -> MeetingRow | None:
        updated_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE meetings
                    SET transcript_text = %s,
                        error_message = %s,
                        status = %s,
                        updated_at = %s
                    WHERE meeting_id = %s
                    RETURNING
                        meeting_id,
                        title,
                        organizer,
                        audio_file_name,
                        stored_file_path,
                        converted_file_path,
                        transcript_text,
                        summary_text,
                        error_message,
                        status,
                        created_at,
                        updated_at
                    """,
                    (
                        transcript_text,
                        error_message,
                        status,
                        updated_at,
                        meeting_id,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()

        if row is None:
            return None

        return MeetingRow(
            meeting_id=row[0],
            title=row[1],
            organizer=row[2],
            audio_file_name=row[3],
            stored_file_path=row[4],
            converted_file_path=row[5],
            transcript_text=row[6],
            summary_text=row[7],
            error_message=row[8],
            status=row[9],
            created_at=row[10],
            updated_at=row[11],
        )

    def update_summary_result(
        self,
        meeting_id: str,
        summary_text: str,
        status: str,
        error_message: str = "",
    ) -> MeetingRow | None:
        updated_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE meetings
                    SET summary_text = %s,
                        error_message = %s,
                        status = %s,
                        updated_at = %s
                    WHERE meeting_id = %s
                    RETURNING
                        meeting_id,
                        title,
                        organizer,
                        audio_file_name,
                        stored_file_path,
                        converted_file_path,
                        transcript_text,
                        summary_text,
                        error_message,
                        status,
                        created_at,
                        updated_at
                    """,
                    (
                        summary_text,
                        error_message,
                        status,
                        updated_at,
                        meeting_id,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()

        if row is None:
            return None

        return MeetingRow(
            meeting_id=row[0],
            title=row[1],
            organizer=row[2],
            audio_file_name=row[3],
            stored_file_path=row[4],
            converted_file_path=row[5],
            transcript_text=row[6],
            summary_text=row[7],
            error_message=row[8],
            status=row[9],
            created_at=row[10],
            updated_at=row[11],
        )
