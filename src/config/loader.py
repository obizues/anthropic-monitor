from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from config.schema import AppConfig, Secrets

_CONFIG_PATH = Path("monitor.config.json")


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {_CONFIG_PATH.resolve()}")
    return AppConfig.model_validate(json.loads(_CONFIG_PATH.read_text()))


@lru_cache(maxsize=1)
def get_secrets() -> Secrets:
    return Secrets()  # type: ignore[call-arg]


def reload_config() -> AppConfig:
    get_config.cache_clear()
    return get_config()
