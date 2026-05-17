"""音频处理服务。"""

from pathlib import Path
from subprocess import CompletedProcess, run

from backend.core.paths import get_abs_path


class AudioService:
    """负责音频转码。"""

    def __init__(self) -> None:
        self._converted_dir = Path(get_abs_path("data/converted"))
        self._converted_dir.mkdir(parents=True, exist_ok=True)

    def build_converted_path(self, meeting_id: str, source_file_name: str) -> Path:
        source_stem = Path(source_file_name).stem or "audio"
        return self._converted_dir / f"{meeting_id}_{source_stem}.wav"

    def convert_to_wav(self, source_path: str, target_path: str) -> CompletedProcess[str]:
        return run(
            [
                "ffmpeg",
                "-y",
                "-i",
                source_path,
                "-ac",
                "1",
                "-ar",
                "16000",
                target_path,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=True,
        )


audio_service = AudioService()
