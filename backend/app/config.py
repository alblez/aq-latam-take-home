from __future__ import annotations

import fnmatch
import re

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded during FastAPI lifespan startup."""

    database_url: str = Field(min_length=1)
    openrouter_api_key: str = Field(min_length=1)
    openrouter_llm_model: str = Field(min_length=1)
    cors_allowed_origins: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


def build_cors_origin_regex(origins_str: str) -> str | None:
    """Convert comma-separated literal/glob origins into one anchored regex."""
    if not origins_str.strip():
        return None

    patterns = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    regex_parts: list[str] = []
    for pattern in patterns:
        if "*" in pattern or "?" in pattern:
            translated = fnmatch.translate(pattern)
            inner = re.sub(r"^\(\?s:", "", translated)
            inner = re.sub(r"\)\\Z$", "", inner)
            regex_parts.append(inner)
        else:
            regex_parts.append(re.escape(pattern))

    return "|".join(f"^{part}$" for part in regex_parts)
