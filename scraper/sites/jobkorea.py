from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from scraper.models import Job

SEARCH_URLS = [
    "https://www.jobkorea.co.kr/Search/?stext=%EB%A1%9C%EB%B4%87+%EC%97%94%EC%A7%80%EB%8B%88%EC%96%B4&tabType=recruit&Page_No={page}",
    "https://www.jobkorea.co.kr/Search/?stext=%EB%A1%9C%EB%B3%B4%ED%8B%B1%EC%8A%A4&tabType=recruit&Page_No={page}",
    "https://www.jobkorea.co.kr/Search/?stext=ROS2+%EC%8B%A0%EC%9E%85&tabType=recruit&Page_No={page}",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


async def scrape_jobkorea() -> list[Job]:
    jobs: list[Job] = []
    seen_ids: set[str] = set()

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        for url_template in SEARCH_URLS:
            for page in range(1, 4):
                url = url_template.format(page=page)
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                except httpx.HTTPError:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                listings = soup.select("article.list-item")

                for item in listings:
                    title_el = item.select_one("a.information-title-link")
                    if not title_el:
                        continue

                    href = title_el.get("href", "")
                    if "/Recruit/GI_Read/" in href:
                        rec_id = href.split("/")[-1].split("?")[0]
                    else:
                        rec_id = href
                    job_id = f"jobkorea_{rec_id}"

                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    title = title_el.get_text(strip=True)
                    company_el = item.select_one("a.company-name-link")
                    company = company_el.get_text(strip=True) if company_el else ""

                    full_url = f"https://www.jobkorea.co.kr{href}" if href.startswith("/") else href

                    loc_el = item.select_one("span.loc")
                    location = loc_el.get_text(strip=True) if loc_el else ""

                    exp_el = item.select_one("span.exp")
                    experience = exp_el.get_text(strip=True) if exp_el else ""

                    date_el = item.select_one("span.date")
                    deadline = date_el.get_text(strip=True) if date_el else ""

                    status = "closed" if "마감" in deadline else "open"

                    jobs.append(Job(
                        id=job_id,
                        title=title,
                        company=company,
                        source="JobKorea",
                        url=full_url,
                        location=location,
                        experience=experience,
                        status=status,
                        deadline=deadline,
                    ))

    return jobs
