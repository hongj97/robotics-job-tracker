from __future__ import annotations

import asyncio
import re

import httpx

from scraper.models import Job

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

MAX_CONCURRENT = 5
DELAY_BETWEEN = 0.5


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 500:
        text = text[:497] + "..."
    return text


async def _fetch_jobkorea_detail(client: httpx.AsyncClient, job: Job) -> str:
    if "/Recruit/GI_Read/" not in job.url and "/Search/" not in job.url:
        return ""
    if "/Search/" in job.url:
        return ""
    try:
        resp = await client.get(job.url)
        resp.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")

        qual_section = soup.select_one("div.tbRow")
        if qual_section:
            items = qual_section.select("dt, dd")
            parts = []
            for item in items:
                txt = item.get_text(strip=True)
                if txt:
                    parts.append(txt)
            return _clean_text(" | ".join(parts))

        desc = soup.select_one("div.viewJobDescription, div.view-detail")
        if desc:
            return _clean_text(desc.get_text(separator=" "))
    except Exception:
        pass
    return ""


async def _fetch_saramin_detail(client: httpx.AsyncClient, job: Job) -> str:
    if "rec_idx=" not in job.url and "/company-info" not in job.url:
        return ""
    try:
        resp = await client.get(job.url)
        resp.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")

        qual = soup.select_one("div.jv_cont.jv_qualification")
        if qual:
            return _clean_text(qual.get_text(separator=" "))

        cont = soup.select_one("div.jv_cont")
        if cont:
            return _clean_text(cont.get_text(separator=" "))
    except Exception:
        pass
    return ""


async def _fetch_wanted_detail(client: httpx.AsyncClient, job: Job) -> str:
    match = re.search(r"/wd/(\d+)", job.url)
    if not match:
        return ""
    wd_id = match.group(1)
    try:
        resp = await client.get(f"https://www.wanted.co.kr/api/v4/jobs/{wd_id}")
        resp.raise_for_status()
        data = resp.json()
        detail = data.get("job", {}).get("detail", {})
        requirements = detail.get("requirements", "")
        if requirements:
            return _clean_text(requirements)
        intro = detail.get("intro", "")
        if intro:
            return _clean_text(intro)
    except Exception:
        pass
    return ""


async def _fetch_jumpit_detail(client: httpx.AsyncClient, job: Job) -> str:
    match = re.search(r"/position/(\d+)", job.url)
    if not match:
        return ""
    pos_id = match.group(1)
    try:
        resp = await client.get(f"https://jumpit.saramin.co.kr/api/position/{pos_id}")
        resp.raise_for_status()
        data = resp.json()
        result = data.get("result", {})
        qualifications = result.get("qualifications", "")
        preferred = result.get("preferredQualifications", "")
        parts = []
        if qualifications:
            parts.append(f"자격요건: {qualifications}")
        if preferred:
            parts.append(f"우대사항: {preferred}")
        if parts:
            return _clean_text(" ".join(parts))
        desc = result.get("content", "")
        if desc:
            from bs4 import BeautifulSoup
            text = BeautifulSoup(desc, "html.parser").get_text(separator=" ")
            return _clean_text(text)
    except Exception:
        pass
    return ""


async def _fetch_rocketpunch_detail(client: httpx.AsyncClient, job: Job) -> str:
    if "/jobs/" not in job.url:
        return ""
    try:
        resp = await client.get(job.url)
        resp.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")

        desc = soup.select_one("div.description.content")
        if desc:
            return _clean_text(desc.get_text(separator=" "))
    except Exception:
        pass
    return ""


FETCHERS = {
    "JobKorea": _fetch_jobkorea_detail,
    "Saramin": _fetch_saramin_detail,
    "Wanted": _fetch_wanted_detail,
    "Jumpit": _fetch_jumpit_detail,
    "Rocketpunch": _fetch_rocketpunch_detail,
}


async def fetch_details_for_jobs(jobs: list[Job]) -> int:
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    updated = 0

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:

        async def process(job: Job) -> None:
            nonlocal updated
            fetcher = FETCHERS.get(job.source)
            if not fetcher:
                return
            async with sem:
                reqs = await fetcher(client, job)
                await asyncio.sleep(DELAY_BETWEEN)
            if reqs:
                job.requirements = reqs
                updated += 1

        tasks = [process(job) for job in jobs]
        await asyncio.gather(*tasks, return_exceptions=True)

    return updated
