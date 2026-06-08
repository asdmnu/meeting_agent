"""FastAPI service entrypoint."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status

from backend.app.schemas import MeetingDetail, MeetingTranscribeResponse, MeetingUploadResponse
from backend.core.config import load_app_config
from backend.core.paths import get_abs_path
from backend.loaders.ensure_meeting_tables import ensure_meeting_tables
from backend.services.meeting_service import meeting_service


ENV_PATH = Path(get_abs_path(".env"))
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)


app_config = load_app_config()
app = FastAPI(title=app_config["app_name"], version="0.2.0")


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database tables on service startup."""
    ensure_meeting_tables()


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/meetings/upload", response_model=MeetingUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_meeting(
    title: str = Form(...),
    organizer: str = Form(...),
    meeting_category: str = Form(""),
    audio_file: UploadFile = File(...),
) -> MeetingUploadResponse:
    """Create a meeting task and upload the original media file."""
    return meeting_service.upload_meeting(
        title=title,
        organizer=organizer,
        meeting_category=meeting_category,
        audio_file=audio_file,
    )


@app.post("/meetings/{meeting_id}/transcribe", response_model=MeetingTranscribeResponse)
def transcribe_meeting_audio(meeting_id: str) -> MeetingTranscribeResponse:
    """Run transcription for one uploaded meeting."""
    return meeting_service.transcribe_meeting_audio(meeting_id)


@app.get("/meetings/{meeting_id}", response_model=MeetingDetail)
def get_meeting(meeting_id: str) -> MeetingDetail:
    """Read one meeting task by id."""
    meeting = meeting_service.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting
