"""ATS providers (Greenhouse, Lever, Workable) через публичные job board API.

Greenhouse и Lever не требуют API-ключа для job board эндпоинтов.
Workable использует публичный widget endpoint для списка вакансий.

Дополнительно можно добавлять свои борды через sources_config.json.
"""

import logging
import time
import json
from typing import List, Dict, Tuple

import requests

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "DevOpsJobMonitor/1.0 (+github.com/YOUR_GITHUB_USERNAME)",
}

RATE_DELAY = 1.0  # секунды между запросами к ATS, чтобы не долбить API


def load_sources_config(config_path: str = "sources_config.json") -> Dict:
    """Загружает конфиг источников ATS, если есть."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"greenhouse": [], "lever": [], "workable": []}
    except Exception as e:
        logger.warning("Failed to load %s: %s", config_path, e)
        return {"greenhouse": [], "lever": [], "workable": []}


def fetch_greenhouse_board(board_token: str) -> List[Dict]:
    """Тянет вакансии через Greenhouse Job Board API.

    Док: https://developers.greenhouse.io/job-board.html
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    jobs: List[Dict] = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Greenhouse %s request failed: %s", board_token, e)
        return jobs
    data = resp.json()
    for item in data.get("jobs", []):
        title = item.get("title") or ""
        company = item.get("company", {}).get("name") if isinstance(item.get("company"), dict) else None
        location = (item.get("location", {}) or {}).get("name") if isinstance(item.get("location"), dict) else None
        url_job = item.get("absolute_url") or item.get("internal_job_id")
        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "url": url_job,
            "source": f"greenhouse:{board_token}",
            "description": "",
            "posted_at": None,
        })
    return jobs


def fetch_lever_board(hostname: str) -> List[Dict]:
    """Тянет вакансии через Lever postings API.

    Док: https://github.com/lever/postings-api
    hostname: поддомен/slug (например, "brightedge" или "remofirst")
    """
    if "/" in hostname:
        hostname = hostname.split("/")[0]
    url = f"https://api.lever.co/v0/postings/{hostname}?mode=json"
    jobs: List[Dict] = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Lever %s request failed: %s", hostname, e)
        return jobs
    data = resp.json()
    for item in data:
        title = item.get("text") or item.get("title") or ""
        company = None
        location = None
        if isinstance(item.get("categories"), dict):
            location = item["categories"].get("location")
        url_job = item.get("hostedUrl") or item.get("applyUrl")
        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "url": url_job,
            "source": f"lever:{hostname}",
            "description": "",
            "posted_at": None,
        })
    return jobs


def fetch_workable_board(account_slug: str) -> List[Dict]:
    """Тянет вакансии через публичный Workable widget API.

    Паттерн описан, например, здесь:
    https://fantastic.jobs/ats/workable
    Endpoint: https://apply.workable.com/api/v1/widget/accounts/{clientname}
    """
    if not account_slug:
        return []
    if "/" in account_slug:
        account_slug = account_slug.split("/")[0]
    url = f"https://apply.workable.com/api/v1/widget/accounts/{account_slug}"
    jobs: List[Dict] = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Workable %s request failed: %s", account_slug, e)
        return jobs
    data = resp.json()
    for item in data.get("jobs", []):
        title = item.get("title") or ""
        location = item.get("location") or None
        url_job = item.get("url") or item.get("applicationUrl")
        jobs.append({
            "title": title,
            "company": None,
            "location": location,
            "url": url_job,
            "source": f"workable:{account_slug}",
            "description": "",
            "posted_at": None,
        })
    return jobs


def fetch_from_config(config: Dict) -> Tuple[List[Dict], Dict[str, str]]:
    """Идёт по конфигу и собирает вакансии из ATS.

    Возвращает список вакансий и словарь статусов по источникам.
    """
    all_jobs: List[Dict] = []
    stats: Dict[str, str] = {}

    for board in config.get("greenhouse", []):
        token = board.get("board_token")
        if not token:
            continue
        key = f"greenhouse:{token}"
        time.sleep(RATE_DELAY)
        try:
            jobs = fetch_greenhouse_board(token)
            stats[key] = f"ok: {len(jobs)}"
        except Exception as e:
            logger.warning("Greenhouse board %s failed: %s", token, e)
            jobs = []
            stats[key] = f"error: {e}"
        all_jobs.extend(jobs)

    for board in config.get("lever", []):
        host = board.get("hostname")
        if not host:
            continue
        key = f"lever:{host}"
        time.sleep(RATE_DELAY)
        try:
            jobs = fetch_lever_board(host)
            stats[key] = f"ok: {len(jobs)}"
        except Exception as e:
            logger.warning("Lever board %s failed: %s", host, e)
            jobs = []
            stats[key] = f"error: {e}"
        all_jobs.extend(jobs)

    for board in config.get("workable", []):
        slug = board.get("account_slug") or board.get("slug") or board.get("hostname")
        if not slug:
            continue
        key = f"workable:{slug}"
        time.sleep(RATE_DELAY)
        try:
            jobs = fetch_workable_board(slug)
            stats[key] = f"ok: {len(jobs)}"
        except Exception as e:
            logger.warning("Workable board %s failed: %s", slug, e)
            jobs = []
            stats[key] = f"error: {e}"
        all_jobs.extend(jobs)

    return all_jobs, stats
