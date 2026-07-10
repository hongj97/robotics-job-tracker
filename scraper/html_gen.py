from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from scraper.models import Job

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs"

SOURCE_DOMAINS = {
    "JobKorea": "jobkorea.co.kr",
    "Saramin": "saramin.co.kr",
    "Wanted": "wanted.co.kr",
    "Jumpit": "jumpit.saramin.co.kr",
    "Rocketpunch": "rocketpunch.com",
}

JUNIOR_KEYWORDS = ["신입", "경력무관", "인턴", "junior", "entry", "0년", "1년", "졸업예정"]


def is_junior_friendly(job: Job) -> bool:
    text = f"{job.experience} {job.title} {job.requirements}".lower()
    return any(kw in text for kw in JUNIOR_KEYWORDS)


def generate_html(jobs: dict[str, Job]) -> None:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    template = env.get_template("index.html.j2")

    by_source: dict[str, list[Job]] = defaultdict(list)
    for job in jobs.values():
        by_source[job.source].append(job)

    for source_jobs in by_source.values():
        source_jobs.sort(key=lambda j: (j.status != "open", j.first_seen), reverse=False)

    source_order = ["JobKorea", "Saramin", "Wanted", "Jumpit", "Rocketpunch"]
    sections = []
    for source in source_order:
        if source in by_source:
            source_jobs = by_source[source]
            sections.append({
                "name": source,
                "domain": SOURCE_DOMAINS.get(source, ""),
                "jobs": source_jobs,
                "total": len(source_jobs),
                "active": sum(1 for j in source_jobs if j.status == "open"),
            })

    for source, source_jobs in by_source.items():
        if source not in source_order:
            sections.append({
                "name": source,
                "domain": "",
                "jobs": source_jobs,
                "total": len(source_jobs),
                "active": sum(1 for j in source_jobs if j.status == "open"),
            })

    total_jobs = len(jobs)
    active_jobs = sum(1 for j in jobs.values() if j.status == "open")
    junior_count = sum(1 for j in jobs.values() if j.status == "open" and is_junior_friendly(j))
    sources_count = len(by_source)
    today = date.today().isoformat()

    html = template.render(
        sections=sections,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        junior_count=junior_count,
        sources_count=sources_count,
        last_updated=today,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "index.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"[html] Generated {output_path}")
