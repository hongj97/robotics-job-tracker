from __future__ import annotations

import httpx

from scraper.models import Job

API_URL = "https://jumpit.saramin.co.kr/api/positions"

PARAMS_LIST = [
    {"keyword": "로봇", "sort": "rsp_rate", "highlight": "false"},
    {"keyword": "로보틱스", "sort": "rsp_rate", "highlight": "false"},
    {"keyword": "ROS", "sort": "rsp_rate", "highlight": "false"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


async def scrape_jumpit() -> list[Job]:
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

            for item in data.get("result", {}).get("positions", []):
                pos_id = str(item.get("id", ""))
                job_id = f"jumpit_{pos_id}"

                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                title = item.get("title", "")
                company = item.get("companyName", "")
                location = item.get("locations", [""])[0] if item.get("locations") else ""

                tech_stacks = [t.get("name", "") for t in item.get("techStacks", [])]

                close_date = item.get("closeDate", "")
                status = "open"
                if close_date:
                    from datetime import date
                    try:
                        deadline_date = date.fromisoformat(close_date[:10])
                        if deadline_date < date.today():
                            status = "closed"
                    except ValueError:
                        pass

                career = item.get("career", "")

                jobs.append(Job(
                    id=job_id,
                    title=title,
                    company=company,
                    source="Jumpit",
                    url=f"https://jumpit.saramin.co.kr/position/{pos_id}",
                    location=location,
                    experience=career,
                    tags=tech_stacks,
                    status=status,
                    deadline=close_date,
                ))

    return jobs
