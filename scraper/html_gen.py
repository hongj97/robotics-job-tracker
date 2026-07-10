from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from scraper.models import Job

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs"


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
                "jobs": source_jobs,
                "total": len(source_jobs),
                "active": sum(1 for j in source_jobs if j.status == "open"),
            })

    for source, source_jobs in by_source.items():
        if source not in source_order:
            sections.append({
                "name": source,
                "jobs": source_jobs,
                "total": len(source_jobs),
                "active": sum(1 for j in source_jobs if j.status == "open"),
            })

    total_jobs = len(jobs)
    active_jobs = sum(1 for j in jobs.values() if j.status == "open")
    sources_count = len(by_source)
    today = date.today().isoformat()

    html = template.render(
        sections=sections,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        sources_count=sources_count,
        last_updated=today,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "index.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"[html] Generated {output_path}")
