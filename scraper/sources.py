import logging
from typing import List, Dict, Tuple

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
}


def fetch_wellfound() -> List[Dict]:
    """Пример парсинга Wellfound DevOps roles in North America."""
    url = "https://wellfound.com/role/l/devops-engineer/north-america"
    jobs: List[Dict] = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Wellfound request failed: %s", e)
        return jobs
    soup = BeautifulSoup(resp.text, "html.parser")
    for card in soup.select("a[href*='/jobs/']"):
        title = (card.get_text(strip=True) or "").strip()
        if not title:
            continue
        href = card.get("href") or ""
        link = href if href.startswith("http") else f"https://wellfound.com{href}"
        jobs.append({
            "title": title,
            "company": None,
            "location": "North America / Remote",
            "url": link,
            "source": "wellfound",
            "description": "",
            "posted_at": None,
        })
    return jobs


def fetch_startup_jobs() -> List[Dict]:
    """Пример парсинга startup.jobs DevOps вакансий."""
    url = "https://startup.jobs/devops-jobs"
    jobs: List[Dict] = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("startup.jobs request failed: %s", e)
        return jobs
    soup = BeautifulSoup(resp.text, "html.parser")
    for card in soup.select(".job-listing, .job, a[href*='/job/']"):
        title_el = card.select_one("h3, .title")
        company_el = card.select_one(".company, .job-listing__company")
        location_el = card.select_one(".location")
        href = card.get("href") or ""
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        company = company_el.get_text(strip=True) if company_el else None
        location = location_el.get_text(strip=True) if location_el else None
        link = href if href.startswith("http") else f"https://startup.jobs{href}"
        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "url": link,
            "source": "startup.jobs",
            "description": "",
            "posted_at": None,
        })
    return jobs


def fetch_yc_workatastartup() -> List[Dict]:
    """Пример парсинга YC Work at a Startup DevOps roles."""
    url = "https://www.workatastartup.com/jobs?team=devops"
    jobs: List[Dict] = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("YC Work at a Startup request failed: %s", e)
        return jobs
    soup = BeautifulSoup(resp.text, "html.parser")
    for card in soup.select("a[href*='/jobs/']"):
        title_el = card.select_one(".job-title, h3")
        company_el = card.select_one(".company-name")
        location_el = card.select_one(".job-location")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        company = company_el.get_text(strip=True) if company_el else None
        location = location_el.get_text(strip=True) if location_el else None
        href = card.get("href") or ""
        link = href if href.startswith("http") else f"https://www.workatastartup.com{href}"
        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "url": link,
            "source": "workatastartup",
            "description": "",
            "posted_at": None,
        })
    return jobs


def fetch_all_sources() -> Tuple[List[Dict], Dict[str, str]]:
    """Вызывает все HTML-источники и возвращает вакансии + статус по источникам."""
    all_jobs: List[Dict] = []
    stats: Dict[str, str] = {}
    for name, fn in (
        ("wellfound", fetch_wellfound),
        ("startup.jobs", fetch_startup_jobs),
        ("workatastartup", fetch_yc_workatastartup),
    ):
        try:
            jobs = fn()
            stats[name] = f"ok: {len(jobs)}"
        except Exception as e:
            logger.warning("Source %s failed: %s", name, e)
            jobs = []
            stats[name] = f"error: {e}"
        all_jobs.extend(jobs)
    return all_jobs, stats
