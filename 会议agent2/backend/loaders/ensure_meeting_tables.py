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
                    meeting_category VARCHAR(100) NOT NULL DEFAULT '',
                    audio_file_name VARCHAR(255) NOT NULL,
                    stored_file_path TEXT NOT NULL DEFAULT '',
                    oss_object_key TEXT NOT NULL DEFAULT '',
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
                ADD COLUMN IF NOT EXISTS meeting_category VARCHAR(100) NOT NULL DEFAULT ''
                """
            )
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN IF NOT EXISTS audio_file_name VARCHAR(255) NOT NULL DEFAULT ''
                """
            )
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN IF NOT EXISTS stored_file_path TEXT NOT NULL DEFAULT ''
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
            cursor.execute(
                """
                ALTER TABLE meetings
                ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'uploaded'
                """
            )
            cursor.execute(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'meetings' AND column_name = 'organizer'
                    ) THEN
                        ALTER TABLE meetings ALTER COLUMN organizer SET DEFAULT '';
                        UPDATE meetings SET organizer = '' WHERE organizer IS NULL;
                        ALTER TABLE meetings ALTER COLUMN organizer DROP NOT NULL;
                    END IF;
                END $$;
                """
            )
        connection.commit()


if __name__ == "__main__":
    ensure_meeting_tables()
