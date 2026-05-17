"""转写服务。"""

from pathlib import Path

from funasr import AutoModel

from backend.core.config import load_asr_config


class TranscriptionService:
    """基于 FunASR 的转写服务。"""

    def __init__(self) -> None:
        self._config = load_asr_config()
        self._model = None

    def _get_model(self):
        if self._model is None:
            model_kwargs = {
                "model": self._config["model"],
                "model_revision": self._config.get("model_revision"),
                "device": self._config.get("device", "cpu"),
                "hub": self._config.get("hub", "ms"),
                "disable_update": self._config.get("disable_update", True),
                "ncpu": self._config.get("ncpu", 4),
            }
            if self._config.get("use_vad", False):
                model_kwargs["vad_model"] = self._config.get("vad_model")
                model_kwargs["vad_model_revision"] = self._config.get("vad_model_revision")
            if self._config.get("use_punc", False):
                model_kwargs["punc_model"] = self._config.get("punc_model")
                model_kwargs["punc_model_revision"] = self._config.get("punc_model_revision")
            self._model = AutoModel(**model_kwargs)
        return self._model

    def transcribe_audio(self, audio_file_path: str) -> str:
        source_path = Path(audio_file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        model = self._get_model()
        result = model.generate(
            input=str(source_path),
            batch_size_s=self._config.get("batch_size_s", 60),
        )
        if not result:
            return ""

        first_item = result[0]
        if isinstance(first_item, dict):
            text = first_item.get("text", "")
            if isinstance(text, str):
                return text.strip()
            if isinstance(text, list):
                return " ".join(str(item) for item in text).strip()

        return str(first_item).strip()


transcription_service = TranscriptionService()
