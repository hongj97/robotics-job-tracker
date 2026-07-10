from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from scraper.models import Job

SEARCH_URLS = [
    "https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword=%EB%A1%9C%EB%B4%87+%EC%97%94%EC%A7%80%EB%8B%88%EC%96%B4&recruitPage={page}",
    "https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword=%EB%A1%9C%EB%B3%B4%ED%8B%B1%EC%8A%A4&recruitPage={page}",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


async def scrape_saramin() -> list[Job]:
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
                listings = soup.select("div.item_recruit")

                for item in listings:
                    title_el = item.select_one("h2.job_tit a")
                    if not title_el:
                        continue

                    href = title_el.get("href", "")
                    rec_idx = ""
                    if "rec_idx=" in href:
                        rec_idx = href.split("rec_idx=")[-1].split("&")[0]
                    job_id = f"saramin_{rec_idx or hash(href)}"

                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    title = title_el.get_text(strip=True)
                    company_el = item.select_one("strong.corp_name a")
                    company = company_el.get_text(strip=True) if company_el else ""

                    full_url = f"https://www.saramin.co.kr{href}" if href.startswith("/") else href

                    conditions = item.select("div.job_condition span")
                    location = conditions[0].get_text(strip=True) if len(conditions) > 0 else ""
                    experience = conditions[1].get_text(strip=True) if len(conditions) > 1 else ""
                    deadline = conditions[-1].get_text(strip=True) if conditions else ""

                    status = "closed" if "마감" in deadline else "open"

                    jobs.append(Job(
                        id=job_id,
                        title=title,
                        company=company,
                        source="Saramin",
                        url=full_url,
                        location=location,
                        experience=experience,
                        status=status,
                        deadline=deadline,
                    ))

    return jobs
