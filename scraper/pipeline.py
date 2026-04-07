import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict

from .filters import is_relevant, priority
from .sources import fetch_all_sources
from .ats_providers import load_sources_config, fetch_from_config

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def canonical_key(job: Dict) -> str:
    """Формирует ключ для дедупликации."""
    parts = [
        (job.get("company") or "").strip().lower(),
        (job.get("title") or "").strip().lower(),
        (job.get("location") or "").strip().lower(),
        (job.get("url") or "").strip().lower(),
    ]
    return "|".join(parts)


def main() -> None:
    logger.info("Fetching raw jobs from HTML sources...")
    raw_html_jobs, html_stats = fetch_all_sources()
    logger.info("HTML sources produced %d jobs", len(raw_html_jobs))

    logger.info("Fetching ATS jobs from config (if any)...")
    config = load_sources_config()
    ats_jobs, ats_stats = fetch_from_config(config)
    logger.info("ATS sources produced %d jobs", len(ats_jobs))

    raw_jobs = raw_html_jobs + ats_jobs
    logger.info("Total raw jobs before filtering: %d", len(raw_jobs))

    filtered = [j for j in raw_jobs if is_relevant(j)]
    logger.info("After relevance filter: %d jobs", len(filtered))

    # Дедупликация
    deduped: Dict[str, Dict] = {}
    for j in filtered:
        key = canonical_key(j)
        if key in deduped:
            # Можно объединять источники, но пока просто сохраняем первый
            continue
        deduped[key] = j

    jobs = list(deduped.values())
    logger.info("After deduplication: %d jobs", len(jobs))

    for j in jobs:
        j["priority"] = priority(j)

    jobs.sort(key=lambda j: (j.get("priority", 4), j.get("title") or ""))

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "jobs.json"

    sources_status: Dict[str, str] = {}
    sources_status.update(html_stats)
    sources_status.update(ats_stats)

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total": len(jobs),
        "jobs": jobs,
        "sources_status": sources_status,
    }

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved %d jobs to %s", len(jobs), out_path)


if __name__ == "__main__":
    main()
