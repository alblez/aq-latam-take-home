"""Strict analyze response parsing (CTRL-03, D-39, D-40, D-41, D-42).

Validates LLM-emitted JSON into typed Flag signals using model_validate_json
(Pattern 3 from RESEARCH: validates raw string directly, not dict + model_validate).
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field

from app.jsonb_schemas import Flag


class AnalyzeResponse(BaseModel):
    """Strict flags-only schema (D-42): only a "flags" key, max 8 entries."""

    model_config = ConfigDict(extra="forbid", strict=True)

    flags: list[Flag] = Field(max_length=8)


def _strip_code_fences(raw: str) -> str:
    """Remove optional ```json ... ``` fences wrapping the output.

    Models often emit fences even when told not to — strip defensively.
    """
    stripped = raw.strip()
    # Match ```json\n...\n``` or ```\n...\n```
    pattern = r"^```(?:json)?\s*\n?(.*?)\n?\s*```$"
    match = re.match(pattern, stripped, re.DOTALL)
    if match:
        return match.group(1).strip()
    return stripped


def parse_analyze_response(raw: str) -> AnalyzeResponse:
    """Parse raw LLM output into validated AnalyzeResponse.

    Uses model_validate_json to accept string UUIDs under strict mode
    (Pitfall 2: Python-mode strict rejects string UUIDs).
    """
    cleaned = _strip_code_fences(raw)
    return AnalyzeResponse.model_validate_json(cleaned)
