from __future__ import annotations

import httpx

from scraper.models import Job

API_URL = "https://www.wanted.co.kr/api/v4/jobs"

PARAMS_LIST = [
    {"country": "kr", "tag_type_ids": "10145", "years": "-1", "locations": "all", "limit": "20", "offset": "0"},
    {"country": "kr", "query": "로보틱스", "limit": "20", "offset": "0"},
    {"country": "kr", "query": "로봇 엔지니어", "limit": "20", "offset": "0"},
    {"country": "kr", "query": "ROS robotics", "limit": "20", "offset": "0"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


async def scrape_wanted() -> list[Job]:
    jobs: list[Job] = []
    seen_ids: set[str] = set()

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        for params in PARAMS_LIST:
            try:
                resp = await client.get(API_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
            except (httpx.HTTPError, ValueError):
                continue

            for item in data.get("data", []):
                wd_id = str(item.get("id", ""))
                job_id = f"wanted_{wd_id}"

                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                title = item.get("position", "")
                company = item.get("company", {}).get("name", "")
                location = item.get("address", {}).get("full_location", "")

                due_time = item.get("due_time")
                if due_time and due_time == "9999-12-31":
                    status = "open"
                    deadline = "상시채용"
                elif due_time:
                    status = "open"
                    deadline = due_time
                else:
                    status = "open"
                    deadline = ""

                jobs.append(Job(
                    id=job_id,
                    title=title,
                    company=company,
                    source="Wanted",
                    url=f"https://www.wanted.co.kr/wd/{wd_id}",
                    location=location,
                    status=status,
                    deadline=deadline,
                ))

    return jobs
