"""会议总结服务。"""

from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.config import load_prompt_config
from backend.core.paths import get_abs_path
from backend.models.factory import get_chat_model


class SummaryService:
    """负责将转写文本整理为会议纪要。"""

    def __init__(self) -> None:
        self._chat_model = get_chat_model()
        self._prompt_config = load_prompt_config()

    def _load_prompt_text(self, config_key: str) -> str:
        prompt_path = Path(get_abs_path(self._prompt_config[config_key]))
        return prompt_path.read_text(encoding="utf-8").strip()

    def summarize_transcript(self, transcript_text: str) -> str:
        system_prompt = self._load_prompt_text("summary_system_prompt_path")
        user_prompt_template = self._load_prompt_text("summary_user_prompt_path")
        user_prompt = user_prompt_template.format(transcript_text=transcript_text)
        response = self._chat_model.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        return str(response.content).strip()


summary_service = SummaryService()
