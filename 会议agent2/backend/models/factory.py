"""模型工厂。"""

from pathlib import Path

from dashscope import TextEmbedding
from dotenv import dotenv_values, load_dotenv
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from backend.core.config import load_model_config
from backend.core.paths import get_abs_path


ENV_PATH = Path(get_abs_path(".env"))
load_dotenv(dotenv_path=ENV_PATH)
ENV_CONFIG = dotenv_values(ENV_PATH)
MODEL_CONFIG = load_model_config()


def get_required_env(key: str) -> str:
    """从 .env 中读取必需的配置值。"""
    value = ENV_CONFIG.get(key, "")
    if not value:
        raise ValueError(f"Missing required config in .env: {key}")
    return value


class DashScopeEmbeddings(Embeddings):
    """最小化的 DashScope 向量封装。"""

    batch_size = 8

    def __init__(self, model: str):
        self.model = model
        self.api_key = get_required_env("MCP_API_KEY")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            response = TextEmbedding.call(
                model=self.model,
                input=batch,
                api_key=self.api_key,
            )
            if not getattr(response, "output", None) or not response.output.get("embeddings"):
                raise ValueError("DashScope embedding response is empty")
            embeddings.extend(item["embedding"] for item in response.output["embeddings"])
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        embeddings = self.embed_documents([text])
        return embeddings[0] if embeddings else []


chat_model = ChatTongyi(
    model=MODEL_CONFIG["chat_model_name"],
    streaming=False,
    dashscope_api_key=get_required_env("MCP_API_KEY"),
)

embedding_model = DashScopeEmbeddings(
    model=MODEL_CONFIG["embedding_model_name"],
)


def get_chat_model() -> BaseChatModel:
    """返回共享的聊天模型实例。"""
    return chat_model


def get_embedding_model() -> Embeddings:
    """返回共享的向量模型实例。"""
    return embedding_model
