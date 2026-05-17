from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

import psycopg

from backend.core.config import load_postgres_config


@dataclass(slots=True)
class MeetingRow:
    meeting_id: str
    title: str
    organizer: str
    audio_file_name: str
    stored_file_path: str
    oss_object_key: str
    transcript_text: str
    clean_transcript_text: str
    summary_json: dict
    summary_text: str
    summary_stage: str
    summary_check_json: dict
    summary_retry_count: int
    needs_human_review: bool
    error_message: str
    status: str
    created_at: datetime
    updated_at: datetime


class MeetingStore:
    def __init__(self) -> None:
        raw_config = load_postgres_config()
        self.host = raw_config["host"]
        self.port = int(raw_config["port"])
        self.database = raw_config["database"]
        self.user = raw_config["user"]
        self.password = raw_config["password"]

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.database} "
            f"user={self.user} password={self.password}"
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
        oss_object_key: str,
    ) -> MeetingRow:
        created_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO meetings (
                        meeting_id, title, organizer, audio_file_name, stored_file_path, oss_object_key,
                        transcript_text, clean_transcript_text, summary_json, summary_text,
                        summary_stage, summary_check_json, summary_retry_count, needs_human_review,
                        error_message, status, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, '', '', '{}'::jsonb, '', '', '{}'::jsonb, 0, FALSE, '', 'uploaded', %s, %s)
                    """,
                    (
                        meeting_id,
                        title,
                        organizer,
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
            organizer=organizer,
            audio_file_name=audio_file_name,
            stored_file_path=stored_file_path,
            oss_object_key=oss_object_key,
            transcript_text="",
            clean_transcript_text="",
            summary_json={},
            summary_text="",
            summary_stage="",
            summary_check_json={},
            summary_retry_count=0,
            needs_human_review=False,
            error_message="",
            status="uploaded",
            created_at=created_at,
            updated_at=created_at,
        )

    def get_meeting(self, meeting_id: str) -> MeetingRow | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT meeting_id, title, organizer, audio_file_name, stored_file_path, oss_object_key,
                           transcript_text, clean_transcript_text, summary_json, summary_text,
                           summary_stage, summary_check_json, summary_retry_count, needs_human_review,
                           error_message, status, created_at, updated_at
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
        updated_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE meetings
                    SET transcript_text = %s, error_message = %s, status = %s, updated_at = %s
                    WHERE meeting_id = %s
                    RETURNING meeting_id, title, organizer, audio_file_name, stored_file_path, oss_object_key,
                              transcript_text, clean_transcript_text, summary_json, summary_text,
                              summary_stage, summary_check_json, summary_retry_count, needs_human_review,
                              error_message, status, created_at, updated_at
                    """,
                    (transcript_text, error_message, status, updated_at, meeting_id),
                )
                row = cursor.fetchone()
            connection.commit()
        return None if row is None else self._build_meeting_row(row)

    def update_summary_result(
        self,
        meeting_id: str,
        clean_transcript_text: str,
        summary_json: dict,
        summary_text: str,
        summary_stage: str,
        summary_check_json: dict,
        summary_retry_count: int,
        needs_human_review: bool,
        status: str,
        error_message: str = "",
    ) -> MeetingRow | None:
        updated_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE meetings
                    SET clean_transcript_text = %s,
                        summary_json = %s,
                        summary_text = %s,
                        summary_stage = %s,
                        summary_check_json = %s,
                        summary_retry_count = %s,
                        needs_human_review = %s,
                        error_message = %s,
                        status = %s,
                        updated_at = %s
                    WHERE meeting_id = %s
                    RETURNING meeting_id, title, organizer, audio_file_name, stored_file_path, oss_object_key,
                              transcript_text, clean_transcript_text, summary_json, summary_text,
                              summary_stage, summary_check_json, summary_retry_count, needs_human_review,
                              error_message, status, created_at, updated_at
                    """,
                    (
                        clean_transcript_text,
                        json.dumps(summary_json, ensure_ascii=False),
                        summary_text,
                        summary_stage,
                        json.dumps(summary_check_json, ensure_ascii=False),
                        summary_retry_count,
                        needs_human_review,
                        error_message,
                        status,
                        updated_at,
                        meeting_id,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()
        return None if row is None else self._build_meeting_row(row)

    def _build_meeting_row(self, row) -> MeetingRow:
        summary_json = row[8]
        if isinstance(summary_json, str):
            try:
                summary_json = json.loads(summary_json)
            except json.JSONDecodeError:
                summary_json = {}
        elif summary_json is None:
            summary_json = {}

        summary_check_json = row[11]
        if isinstance(summary_check_json, str):
            try:
                summary_check_json = json.loads(summary_check_json)
            except json.JSONDecodeError:
                summary_check_json = {}
        elif summary_check_json is None:
            summary_check_json = {}

        return MeetingRow(
            meeting_id=row[0],
            title=row[1],
            organizer=row[2],
            audio_file_name=row[3],
            stored_file_path=row[4],
            oss_object_key=row[5],
            transcript_text=row[6],
            clean_transcript_text=row[7],
            summary_json=summary_json,
            summary_text=row[9],
            summary_stage=row[10],
            summary_check_json=summary_check_json,
            summary_retry_count=row[12],
            needs_human_review=row[13],
            error_message=row[14],
            status=row[15],
            created_at=row[16],
            updated_at=row[17],
        )
