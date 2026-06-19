"""History endpoint — owner-scoped terminal session list with derived metrics."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.deps import DbSession, OwnerId
from app.history_detail import assemble_history_response
from app.schemas import HistoryResponse

router = APIRouter(tags=["history"])


@router.get("/history", response_model=HistoryResponse)
def list_history(
    owner_id: OwnerId,
    db: DbSession,
    jobId: UUID | None = None,
) -> HistoryResponse:
    """List terminal sessions for the requesting owner with derived analytics.

    Supports optional jobId filter. Returns 200 with empty list for no matches.
    All metrics derived at read time from relational data (no persisted aggregates).
    """
    return assemble_history_response(db, owner_id, job_id=jobId)
