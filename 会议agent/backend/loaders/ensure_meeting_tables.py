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
                    converted_file_path TEXT NOT NULL DEFAULT '',
                    transcript_text TEXT NOT NULL DEFAULT '',
                    summary_text TEXT NOT NULL DEFAULT '',
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
                ADD COLUMN IF NOT EXISTS converted_file_path TEXT NOT NULL DEFAULT ''
                """
            )
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN IF NOT EXISTS transcript_text TEXT NOT NULL DEFAULT ''
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
                ADD COLUMN IF NOT EXISTS error_message TEXT NOT NULL DEFAULT ''
                """
            )
        connection.commit()


if __name__ == "__main__":
    ensure_meeting_tables()
