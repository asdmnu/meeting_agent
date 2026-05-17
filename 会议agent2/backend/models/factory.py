from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.language_models import BaseChatModel

from backend.core.config import load_model_config
from backend.core.paths import get_abs_path


ENV_PATH = Path(get_abs_path(".env"))
load_dotenv(dotenv_path=ENV_PATH)
ENV_CONFIG = dotenv_values(ENV_PATH)
MODEL_CONFIG = load_model_config()


def get_required_env(key: str) -> str:
    value = ENV_CONFIG.get(key, "")
    if not value:
        raise ValueError(f"Missing required key in .env: {key}")
    return value


def get_chat_model() -> BaseChatModel:
    return ChatTongyi(
        model=MODEL_CONFIG["chat_model_name"],
        streaming=False,
        dashscope_api_key=get_required_env("DASHSCOPE_API_KEY"),
    )
