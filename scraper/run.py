from __future__ import annotations

import asyncio
import sys

from scraper.models import load_jobs, save_jobs
from scraper.sites import ALL_SCRAPERS
from scraper.diff import compute_diff
from scraper.discord_notify import send_discord_notification
from scraper.html_gen import generate_html


async def scrape_all() -> list:
    from scraper.models import Job

    all_jobs: list[Job] = []
    for scraper_fn in ALL_SCRAPERS:
        try:
            print(f"[scraper] Running {scraper_fn.__name__}...")
            jobs = await scraper_fn()
            print(f"[scraper] {scraper_fn.__name__}: {len(jobs)} jobs found")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[scraper] {scraper_fn.__name__} failed: {e}")
    return all_jobs


def main():
    print("[main] Loading previous job data...")
    old_jobs = load_jobs()
    print(f"[main] Previously tracked: {len(old_jobs)} jobs")

    print("[main] Scraping all sites...")
    fresh_jobs = asyncio.run(scrape_all())
    print(f"[main] Fresh scrape total: {len(fresh_jobs)} jobs")

    print("[main] Computing diff...")
    merged, diff = compute_diff(old_jobs, fresh_jobs)
    print(f"[main] New: {len(diff.new_jobs)}, Closed: {len(diff.closed_jobs)}, Active: {diff.total_active}")

    print("[main] Saving updated job data...")
    save_jobs(merged)

    print("[main] Generating HTML report...")
    generate_html(merged)

    pages_url = ""
    if len(sys.argv) > 1:
        pages_url = sys.argv[1]

    if diff.new_jobs or diff.closed_jobs or diff.reopened_jobs:
        print("[main] Sending Discord notification...")
        send_discord_notification(diff, pages_url)
    else:
        print("[main] No changes detected, skipping notification")

    print("[main] Done!")


if __name__ == "__main__":
    main()
