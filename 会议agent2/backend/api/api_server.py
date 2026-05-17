from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status

from backend.api.schemas import (
    MeetingDetail,
    MeetingSummarizeResponse,
    MeetingTranscribeResponse,
    MeetingUploadResponse,
)
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
    ensure_meeting_tables()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/meetings/upload", response_model=MeetingUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_meeting(title: str = Form(...), organizer: str = Form(...), audio_file: UploadFile = File(...)) -> MeetingUploadResponse:
    return meeting_service.upload_meeting(title=title, organizer=organizer, audio_file=audio_file)


@app.post("/meetings/{meeting_id}/transcribe", response_model=MeetingTranscribeResponse)
def transcribe_meeting_audio(meeting_id: str) -> MeetingTranscribeResponse:
    return meeting_service.transcribe_meeting_audio(meeting_id)


@app.post("/meetings/{meeting_id}/summarize", response_model=MeetingSummarizeResponse)
def summarize_meeting(meeting_id: str) -> MeetingSummarizeResponse:
    return meeting_service.summarize_meeting(meeting_id)


@app.get("/meetings/{meeting_id}", response_model=MeetingDetail)
def get_meeting(meeting_id: str) -> MeetingDetail:
    meeting = meeting_service.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting
