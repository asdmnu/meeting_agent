from pathlib import Path

import yaml

from backend.core.paths import get_abs_path


def _load_yaml_config(config_path: str, encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def load_app_config(config_path: str = get_abs_path("backend/config/app.yml"), encoding: str = "utf-8"):
    """从 YAML 配置中加载应用设置。"""
    return _load_yaml_config(config_path, encoding)


def load_postgres_config(config_path: str = get_abs_path("backend/config/postgres.yml"), encoding: str = "utf-8"):
    """从 YAML 配置中加载 PostgreSQL 设置。"""
    return _load_yaml_config(config_path, encoding)


def load_mcp_config(config_path: str = get_abs_path("backend/config/mcp.yml"), encoding: str = "utf-8"):
    """从 YAML 配置中加载 MCP 服务设置。"""
    return _load_yaml_config(config_path, encoding)


def load_model_config(config_path: str = get_abs_path("backend/config/models.yml"), encoding: str = "utf-8"):
    """从 YAML 配置中加载模型设置。"""
    return _load_yaml_config(config_path, encoding)


def load_prompt_config(config_path: str = get_abs_path("backend/config/prompts.yml"), encoding: str = "utf-8"):
    """从 YAML 配置中加载提示词路径设置。"""
    return _load_yaml_config(config_path, encoding)


def load_rag_config(config_path: str = get_abs_path("backend/config/rag.yml"), encoding: str = "utf-8"):
    """从 YAML 配置中加载 RAG 设置。"""
    return _load_yaml_config(config_path, encoding)


def load_frontend_config(config_path: str = get_abs_path("frontend/config/app.yml"), encoding: str = "utf-8"):
    """从 YAML 配置中加载前端设置。"""
    return _load_yaml_config(config_path, encoding)


def _load_prompt(path_key: str) -> str:
    prompt_config = load_prompt_config()
    prompt_path = Path(get_abs_path(prompt_config[path_key]))
    return prompt_path.read_text(encoding="utf-8").strip()


def load_content_prompt() -> str:
    """加载内容分析提示词模板。"""
    return _load_prompt("content_prompt_path")


def load_task_prompt() -> str:
    """加载任务分析提示词模板。"""
    return _load_prompt("task_prompt_path")


def load_risk_prompt() -> str:
    """加载风险分析提示词模板。"""
    return _load_prompt("risk_prompt_path")


def load_rag_decider_prompt() -> str:
    """加载 RAG 决策提示词模板。"""
    return _load_prompt("rag_decider_prompt_path")


def load_summary_prompt() -> str:
    """加载会议总结提示词模板。"""
    return _load_prompt("summary_prompt_path")
