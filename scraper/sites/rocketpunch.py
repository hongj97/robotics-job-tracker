from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from scraper.models import Job

SEARCH_URLS = [
    "https://www.rocketpunch.com/jobs?keywords=%EB%A1%9C%EB%B4%87&page={page}",
    "https://www.rocketpunch.com/jobs?keywords=%EB%A1%9C%EB%B3%B4%ED%8B%B1%EC%8A%A4&page={page}",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


async def scrape_rocketpunch() -> list[Job]:
    jobs: list[Job] = []
    seen_ids: set[str] = set()

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        for url_template in SEARCH_URLS:
            for page in range(1, 3):
                url = url_template.format(page=page)
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                except httpx.HTTPError:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                listings = soup.select("div.job-item")

                for item in listings:
                    link_el = item.select_one("a.job-title")
                    if not link_el:
                        continue

                    href = link_el.get("href", "")
                    job_num = href.rstrip("/").split("/")[-1] if "/jobs/" in href else href
                    job_id = f"rocketpunch_{job_num}"

                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    title = link_el.get_text(strip=True)

                    company_el = item.select_one("a.company-name")
                    company = company_el.get_text(strip=True) if company_el else ""

                    full_url = f"https://www.rocketpunch.com{href}" if href.startswith("/") else href

                    location_el = item.select_one("span.location")
                    location = location_el.get_text(strip=True) if location_el else ""

                    career_el = item.select_one("span.career")
                    experience = career_el.get_text(strip=True) if career_el else ""

                    tag_els = item.select("a.tag")
                    tags = [t.get_text(strip=True) for t in tag_els]

                    jobs.append(Job(
                        id=job_id,
                        title=title,
                        company=company,
                        source="Rocketpunch",
                        url=full_url,
                        location=location,
                        experience=experience,
                        tags=tags,
                        status="open",
                    ))

    return jobs
