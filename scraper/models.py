from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path

JOBS_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.json"


@dataclass
class Job:
    id: str
    title: str
    company: str
    source: str
    url: str
    location: str = ""
    experience: str = ""
    requirements: str = ""
    tags: list[str] = field(default_factory=list)
    status: str = "open"
    first_seen: str = ""
    last_seen: str = ""
    deadline: str = ""

    def __post_init__(self):
        today = date.today().isoformat()
        if not self.first_seen:
            self.first_seen = today
        if not self.last_seen:
            self.last_seen = today


def load_jobs() -> dict[str, Job]:
    if not JOBS_PATH.exists():
        return {}
    raw = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    return {k: Job(**v) for k, v in raw.items()}


def save_jobs(jobs: dict[str, Job]) -> None:
    JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {k: asdict(v) for k, v in jobs.items()}
    JOBS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
