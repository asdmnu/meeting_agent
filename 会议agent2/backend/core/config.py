import os

import yaml

from backend.core.paths import get_abs_path


def _load_yaml_config(config_path: str, encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def load_app_config(config_path: str = get_abs_path("backend/config/app.yml"), encoding: str = "utf-8"):
    config = _load_yaml_config(config_path, encoding)
    for key, env_key in {
        "app_name": "APP_NAME",
        "app_env": "APP_ENV",
        "api_host": "API_HOST",
        "api_port": "API_PORT",
        "upload_dir": "UPLOAD_DIR",
        "log_dir": "LOG_DIR",
    }.items():
        value = os.getenv(env_key)
        if value not in (None, ""):
            config[key] = value
    return config


def load_postgres_config(config_path: str = get_abs_path("backend/config/postgres.yml"), encoding: str = "utf-8"):
    config = _load_yaml_config(config_path, encoding)
    for key, env_key in {
        "host": "POSTGRES_HOST",
        "port": "POSTGRES_PORT",
        "database": "POSTGRES_DB",
        "user": "POSTGRES_USER",
        "password": "POSTGRES_PASSWORD",
    }.items():
        value = os.getenv(env_key)
        if value not in (None, ""):
            config[key] = value
    return config


def load_mcp_config(config_path: str = get_abs_path("backend/config/mcp.yml"), encoding: str = "utf-8"):
    return _load_yaml_config(config_path, encoding)


def load_model_config(config_path: str = get_abs_path("backend/config/models.yml"), encoding: str = "utf-8"):
    return _load_yaml_config(config_path, encoding)


def load_prompt_config(config_path: str = get_abs_path("backend/config/prompts.yml"), encoding: str = "utf-8"):
    return _load_yaml_config(config_path, encoding)
