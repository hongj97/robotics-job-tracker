from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from scraper.models import Job


@dataclass
class DiffResult:
    new_jobs: list[Job] = field(default_factory=list)
    closed_jobs: list[Job] = field(default_factory=list)
    reopened_jobs: list[Job] = field(default_factory=list)
    total_active: int = 0


def compute_diff(old: dict[str, Job], fresh: list[Job]) -> tuple[dict[str, Job], DiffResult]:
    today = date.today().isoformat()
    result = DiffResult()

    fresh_by_id = {j.id: j for j in fresh}

    merged = dict(old)

    for job_id, job in fresh_by_id.items():
        if job_id not in merged:
            job.first_seen = today
            job.last_seen = today
            merged[job_id] = job
            result.new_jobs.append(job)
        else:
            existing = merged[job_id]
            existing.last_seen = today
            existing.title = job.title
            existing.url = job.url
            existing.deadline = job.deadline or existing.deadline
            existing.tags = job.tags or existing.tags

            if existing.status == "closed" and job.status == "open":
                existing.status = "open"
                result.reopened_jobs.append(existing)
            elif job.status == "open":
                existing.status = "open"

    for job_id, job in merged.items():
        if job_id not in fresh_by_id and job.status == "open":
            if job.last_seen < today:
                job.status = "closed"
                result.closed_jobs.append(job)

    result.total_active = sum(1 for j in merged.values() if j.status == "open")

    return merged, result
