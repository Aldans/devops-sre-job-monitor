KEYWORDS_INCLUDE = [
    "devops",
    "site reliability",
    "sre",
    "platform engineer",
    "platform engineering",
    "infrastructure",
    "cloud engineer",
    "cloud infrastructure",
    "infra engineer",
    "kubernetes",
    "terraform",
    "gitops",
]

BLOCKED = [
    "clearance",
    "security clearance",
    "ts/sci",
    "ts / sci",
    "top secret",
    "us citizen only",
    "u.s. citizen only",
    "must be us citizen",
    "must be a us citizen",
    "green card required",
    "us person",
    "citizenship required",
    "must hold us citizenship",
]

LA_KEYWORDS = [
    "los angeles",
    "hawthorne",
    "culver city",
    "santa monica",
    "burbank",
]

IRVINE_KEYWORDS = [
    "irvine",
    "newport beach",
    "costa mesa",
    "tustin",
]


def is_relevant(job: dict) -> bool:
    """Возвращает True, если вакансия похожа на DevOps/SRE и не содержит стоп-слов."""
    text = (job.get("title", "") + " " + job.get("description", "")).lower()
    if not any(k in text for k in KEYWORDS_INCLUDE):
        return False
    if any(b in text for b in BLOCKED):
        return False
    return True


def priority(job: dict) -> int:
    """Присваивает приоритет по локации."""
    loc = (job.get("location") or "").lower()
    if "remote" in loc:
        return 1
    if any(k in loc for k in LA_KEYWORDS + IRVINE_KEYWORDS):
        return 2
    if "california" in loc or ", ca" in loc:
        return 3
    return 4
