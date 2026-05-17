from backend.stores.meeting_store import MeetingStore


def ensure_meeting_tables() -> None:
    store = MeetingStore()
    with store._connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS meetings (
                    meeting_id VARCHAR(36) PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    organizer VARCHAR(100) NOT NULL,
                    audio_file_name VARCHAR(255) NOT NULL,
                    stored_file_path TEXT NOT NULL DEFAULT '',
                    oss_object_key TEXT NOT NULL DEFAULT '',
                    transcript_text TEXT NOT NULL DEFAULT '',
                    clean_transcript_text TEXT NOT NULL DEFAULT '',
                    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    summary_text TEXT NOT NULL DEFAULT '',
                    summary_stage VARCHAR(32) NOT NULL DEFAULT '',
                    summary_check_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    summary_retry_count INTEGER NOT NULL DEFAULT 0,
                    needs_human_review BOOLEAN NOT NULL DEFAULT FALSE,
                    error_message TEXT NOT NULL DEFAULT '',
                    status VARCHAR(32) NOT NULL DEFAULT 'uploaded',
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN IF NOT EXISTS oss_object_key TEXT NOT NULL DEFAULT ''
                """
            )
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN IF NOT EXISTS summary_text TEXT NOT NULL DEFAULT ''
                """
            )
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN IF NOT EXISTS clean_transcript_text TEXT NOT NULL DEFAULT ''
                """
            )
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN IF NOT EXISTS summary_json JSONB NOT NULL DEFAULT '{}'::jsonb
                """
            )
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN IF NOT EXISTS summary_stage VARCHAR(32) NOT NULL DEFAULT ''
                """
            )
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN IF NOT EXISTS summary_check_json JSONB NOT NULL DEFAULT '{}'::jsonb
                """
            )
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN IF NOT EXISTS summary_retry_count INTEGER NOT NULL DEFAULT 0
                """
            )
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN IF NOT EXISTS needs_human_review BOOLEAN NOT NULL DEFAULT FALSE
                """
            )
        connection.commit()


if __name__ == "__main__":
    ensure_meeting_tables()
