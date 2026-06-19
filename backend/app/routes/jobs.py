from __future__ import annotations

from fastapi import APIRouter

from app.deps import DbSession
from app.repositories import list_jobs_with_counts
from app.schemas import Job, JobListResponse

router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(db: DbSession) -> JobListResponse:
    """List persisted jobs with live competency counts. Excludes zero-competency jobs."""
    rows = list_jobs_with_counts(db)
    jobs = [
        Job(
            id=job.id,
            title=job.title,
            description=job.description,
            competencyCount=count,
        )
        for job, count in rows
    ]
    return JobListResponse(jobs=jobs)
