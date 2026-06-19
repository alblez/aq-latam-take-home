"""Single model-gateway boundary (CTRL-01, D-06, D-17).

All OpenRouter HTTP calls go through this module. No other module in app/
imports httpx2 or touches the API key.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
from uuid import UUID

import httpx2
import structlog

if TYPE_CHECKING:
    from app.engine.analyze import AnalyzeResponse
    from app.engine.evaluation import ModelEvaluationResponse
    from app.engine.prompts import CompetencyBrief, TranscriptTurn
    from app.jsonb_schemas import Flag

# --- Module constants (D-22, D-23) ---

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
ANALYZE_TEMPERATURE = 0.0  # D-23: max repeatability for signal extraction
GENERATE_TEMPERATURE = 0.2  # D-23: slight creativity for question phrasing
ANALYZE_MAX_TOKENS = 1024
GENERATE_MAX_TOKENS = 200  # ~40-word question bound
CALL_TIMEOUT = httpx2.Timeout(30.0, connect=10.0)  # D-22: generous ~30s budget

# Evaluation-specific budgets (D-04, D-06)
EVALUATION_TEMPERATURE = 0.0
EVALUATION_MAX_TOKENS = 2200
EVALUATION_TIMEOUT = httpx2.Timeout(60.0, connect=10.0)

logger = structlog.get_logger()

# --- Exception hierarchy (D-26) ---


class GatewayError(Exception):
    """Base for all gateway failures."""


class GatewayTimeout(GatewayError):
    """Transport timeout (connect or read)."""


class GatewayHTTPError(GatewayError):
    """Non-200 status or transport-level HTTP error (including 429)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_text: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class GatewayParseError(GatewayError):
    """Provider response is malformed or empty."""


# --- Helpers ---


def _evaluation_response_format() -> dict[str, object]:
    """Build response_format payload for structured evaluation output."""
    from app.engine.evaluation import ModelEvaluationResponse

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "interview_evaluation_v1",
            "strict": True,
            "schema": ModelEvaluationResponse.model_json_schema(),
        },
    }


def _is_response_format_rejection(exc: GatewayHTTPError) -> bool:
    """Detect if a 400 error is due to provider rejecting response_format/json_schema."""
    if exc.status_code != 400:
        return False
    text = (exc.response_text or "") + str(exc)
    text_lower = text.lower()
    return any(kw in text_lower for kw in ("response_format", "json_schema", "structured"))


# --- Protocol for test fakes (D-07) ---


class ModelGateway(Protocol):
    """Typed contract for the gateway — enables test fakes."""

    @property
    def model_name(self) -> str: ...  # pragma: no cover

    def analyze_answer(
        self,
        *,
        transcript: list[TranscriptTurn],
        competencies: list[CompetencyBrief],
    ) -> AnalyzeResponse: ...  # pragma: no cover

    def generate_question(self, *, messages: list[dict[str, str]]) -> str: ...  # pragma: no cover

    def evaluate_session(
        self,
        *,
        transcript: list[TranscriptTurn],
        competencies: list[CompetencyBrief],
        flags: list[Flag],
        coverage: dict[UUID, str],
        terminal_reason: str,
    ) -> ModelEvaluationResponse: ...  # pragma: no cover


# --- Concrete gateway ---


class OpenRouterGateway:
    """Sync httpx2 gateway to OpenRouter chat completions (D-17, D-18).

    Constructor takes explicit args — nothing in this module reads env or Settings
    at import time (Pitfall 3).
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = OPENROUTER_BASE_URL,
        transport: httpx2.BaseTransport | None = None,
    ) -> None:
        self._model = model
        self._client = httpx2.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=CALL_TIMEOUT,
            transport=transport,
        )

    @property
    def model_name(self) -> str:
        """Model identifier passed at construction (D-05 write-once source)."""
        return self._model

    def close(self) -> None:
        """Close the underlying httpx2 client."""
        self._client.close()

    # --- Private transport (Pattern 2) ---

    def _chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
        response_format: dict[str, object] | None = None,
        timeout: httpx2.Timeout | None = None,
    ) -> str:
        """Single POST to /chat/completions with typed exception mapping."""
        payload: dict[str, object] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format is not None:
            payload["response_format"] = response_format

        try:
            if timeout is not None:
                response = self._client.post(
                    "/chat/completions",
                    json=payload,
                    timeout=timeout,
                )
            else:
                response = self._client.post(
                    "/chat/completions",
                    json=payload,
                )
        except httpx2.TimeoutException as exc:
            raise GatewayTimeout(exc.__class__.__name__) from exc
        except httpx2.HTTPError as exc:
            raise GatewayHTTPError(exc.__class__.__name__) from exc

        if response.status_code != 200:
            raise GatewayHTTPError(
                f"status_{response.status_code}",
                status_code=response.status_code,
                response_text=response.text[:500],
            )

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise GatewayParseError("malformed_provider_response") from exc

        if not isinstance(content, str) or not content.strip():
            raise GatewayParseError("empty_content")

        return content

    def _chat_with_retry(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
        response_format: dict[str, object] | None = None,
        timeout: httpx2.Timeout | None = None,
    ) -> str:
        """Two-attempt loop: retry ONLY GatewayTimeout/GatewayHTTPError once (D-20).

        Parse errors are NOT retried at the transport level.
        """
        last_exc: GatewayError | None = None
        for _attempt in range(2):
            try:
                return self._chat(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    timeout=timeout,
                )
            except (GatewayTimeout, GatewayHTTPError) as exc:
                last_exc = exc
                continue
            except GatewayParseError:
                raise  # parse errors: no transport retry
        # Both attempts failed — log at error level (D-24: final failure only)
        logger.error("gateway_transport_failed", model=self._model, error=str(last_exc))
        raise last_exc  # type: ignore[misc] -- always set after 2 iterations

    # --- Public typed methods (D-07) ---

    def analyze_answer(
        self,
        *,
        transcript: list[TranscriptTurn],
        competencies: list[CompetencyBrief],
    ) -> AnalyzeResponse:
        """Analyze candidate answer into validated Flag signals (D-07, D-19).

        One repair retry on validation failure, then GatewayParseError.
        """
        from pydantic import ValidationError

        from app.engine.analyze import parse_analyze_response
        from app.engine.prompts import build_analyze_messages, build_repair_messages

        messages = build_analyze_messages(transcript, competencies)
        raw = self._chat_with_retry(
            messages, temperature=ANALYZE_TEMPERATURE, max_tokens=ANALYZE_MAX_TOKENS
        )

        try:
            return parse_analyze_response(raw)
        except ValidationError as first_exc:
            # ONE repair retry (D-19): send validation error back
            repair_msgs = messages + build_repair_messages(raw, str(first_exc))
            try:
                repair_raw = self._chat_with_retry(
                    repair_msgs, temperature=ANALYZE_TEMPERATURE, max_tokens=ANALYZE_MAX_TOKENS
                )
                return parse_analyze_response(repair_raw)
            except ValidationError as second_exc:
                raise GatewayParseError("analyze_validation_failed") from second_exc

    def generate_question(self, *, messages: list[dict[str, str]]) -> str:
        """Generate a phrased question from pre-built messages (D-07).

        Accepts pre-built messages from follow-up/new-topic builders.
        """
        content = self._chat_with_retry(
            messages, temperature=GENERATE_TEMPERATURE, max_tokens=GENERATE_MAX_TOKENS
        )
        return content.strip()

    def evaluate_session(
        self,
        *,
        transcript: list[TranscriptTurn],
        competencies: list[CompetencyBrief],
        flags: list[Flag],
        coverage: dict[UUID, str],
        terminal_reason: str,
    ) -> ModelEvaluationResponse:
        """Evaluate full session: D-02 single comprehensive call with D-03 repair.

        Flow:
        1. POST with response_format (structured output hint)
        2. If provider rejects format (400 with json_schema text) → retry without format
        3. Parse + alignment validate
        4. On failure → ONE repair retry
        5. Second failure → GatewayParseError("evaluation_validation_failed")
        """
        from pydantic import ValidationError

        from app.engine.evaluation import (
            EvaluationAlignmentError,
            parse_evaluation_response,
            validate_competency_alignment,
        )
        from app.engine.prompts import (
            build_evaluation_messages,
            build_evaluation_repair_messages,
        )

        messages = build_evaluation_messages(
            transcript, competencies, flags, coverage, terminal_reason
        )
        expected_ids = {c.id for c in competencies}
        unprobed_ids = {cid for cid, s in coverage.items() if s == "not-reached"}

        # Attempt with structured output format
        resp_format = _evaluation_response_format()
        try:
            raw = self._chat_with_retry(
                messages,
                temperature=EVALUATION_TEMPERATURE,
                max_tokens=EVALUATION_MAX_TOKENS,
                response_format=resp_format,
                timeout=EVALUATION_TIMEOUT,
            )
        except GatewayHTTPError as exc:
            if _is_response_format_rejection(exc):
                # Fallback: retry without response_format
                raw = self._chat_with_retry(
                    messages,
                    temperature=EVALUATION_TEMPERATURE,
                    max_tokens=EVALUATION_MAX_TOKENS,
                    timeout=EVALUATION_TIMEOUT,
                )
            else:
                raise

        # Parse + alignment gate with one repair retry (D-03)
        try:
            parsed = parse_evaluation_response(raw)
            validate_competency_alignment(
                parsed, expected_ids=expected_ids, unprobed_ids=unprobed_ids
            )
            return parsed
        except (ValidationError, EvaluationAlignmentError) as first_exc:
            # ONE repair retry
            repair_msgs = messages + build_evaluation_repair_messages(raw, str(first_exc))
            try:
                repair_raw = self._chat_with_retry(
                    repair_msgs,
                    temperature=EVALUATION_TEMPERATURE,
                    max_tokens=EVALUATION_MAX_TOKENS,
                    timeout=EVALUATION_TIMEOUT,
                )
                parsed = parse_evaluation_response(repair_raw)
                validate_competency_alignment(
                    parsed, expected_ids=expected_ids, unprobed_ids=unprobed_ids
                )
                return parsed
            except (ValidationError, EvaluationAlignmentError) as second_exc:
                raise GatewayParseError("evaluation_validation_failed") from second_exc
