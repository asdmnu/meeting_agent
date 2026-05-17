import os

import yaml

from backend.core.paths import get_abs_path


def _load_yaml_config(config_path: str, encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def load_app_config(
    config_path: str = get_abs_path("backend/config/app.yml"),
    encoding: str = "utf-8",
):
    config = _load_yaml_config(config_path, encoding)
    env_overrides = {
        "app_name": os.getenv("APP_NAME"),
        "app_env": os.getenv("APP_ENV"),
        "api_host": os.getenv("API_HOST"),
        "api_port": os.getenv("API_PORT"),
        "database_url": os.getenv("DATABASE_URL"),
        "upload_dir": os.getenv("UPLOAD_DIR"),
        "log_dir": os.getenv("LOG_DIR"),
    }
    for key, value in env_overrides.items():
        if value not in (None, ""):
            config[key] = value
    return config


def load_postgres_config(
    config_path: str = get_abs_path("backend/config/postgres.yml"),
    encoding: str = "utf-8",
):
    config = _load_yaml_config(config_path, encoding)
    env_overrides = {
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
        "database": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }
    for key, value in env_overrides.items():
        if value not in (None, ""):
            config[key] = value
    return config


def load_asr_config(
    config_path: str = get_abs_path("backend/config/asr.yml"),
    encoding: str = "utf-8",
):
    return _load_yaml_config(config_path, encoding)


def load_model_config(
    config_path: str = get_abs_path("backend/config/models.yml"),
    encoding: str = "utf-8",
):
    return _load_yaml_config(config_path, encoding)


def load_prompt_config(
    config_path: str = get_abs_path("backend/config/prompts.yml"),
    encoding: str = "utf-8",
):
    return _load_yaml_config(config_path, encoding)
