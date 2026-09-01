from datetime import datetime, timezone

from api.core import jobs_config


def _haystack(job: dict) -> str:
    parts = [
        job.get("title"), job.get("skills"), job.get("ai_technical_skills"),
        job.get("description"), job.get("ai_inferred_technical_skills"),
        job.get("ai_named_entities"),
    ]
    return " ".join("" if p is None else str(p) for p in parts).lower()


def _excluded_country(job: dict) -> bool:
    loc = f"{job.get('client_location') or ''} {job.get('buyer_city') or ''}".lower()
    return any(c in loc for c in jobs_config.EXCLUDE_COUNTRIES)


def expand_keywords(keywords: list[str]) -> list[str]:
    """Turn profile keywords into substrings that actually occur in job text.

    Profile keywords are written for humans ("Redux / Redux Toolkit",
    "JavaScript (ES6+)"), and those exact strings never appear in a posting.
    Split on "/" and drop parenthetical suffixes so each alternative can match
    on its own, while keeping multi-word phrases intact ("mern stack" must not
    degrade into a bare "stack", which would match almost any job).
    """
    out = []
    for raw in keywords:
        for part in str(raw).split("/"):
            part = part.split("(")[0].strip().lower()
            if part:
                out.append(part)
    return out


def _too_old(job: dict) -> bool:
    date_posted = job.get("date_posted")
    if not date_posted:
        return False
    try:
        posted = datetime.fromisoformat(str(date_posted).replace("Z", "+00:00"))
    except ValueError:
        return False
    if posted.tzinfo is None:
        posted = posted.replace(tzinfo=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - posted).total_seconds() / 3600
    return age_hours > jobs_config.MAX_AGE_HOURS


def filter_relevant(
    jobs: list[dict],
    apply_stack_filters: bool = True,
    match_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
) -> list[dict]:
    """Hard filters (payment/country/age) always apply.

    `match_keywords` is the profile-driven path: keep a job matching ANY of the
    profile's keywords. This has to happen here rather than in the Apify query,
    because the actor ANDs multi-term `skills`/`keywords` filters — asking it for
    20 skills at once matches no job at all.

    `apply_stack_filters` is the legacy no-profile path: the global stack
    keywords plus platform-lock/title exclusions, which encode one freelancer's
    default dev stack and don't generalise to arbitrary niches.
    """
    expanded = expand_keywords(match_keywords) if match_keywords else None
    banned = expand_keywords(exclude_keywords) if exclude_keywords else None

    out = []
    for job in jobs:
        if jobs_config.REQUIRE_PAYMENT_VERIFIED and not job.get("buyer_payment_verified"):
            continue
        if _excluded_country(job):
            continue
        if _too_old(job):
            continue

        # The actor's own exclude_keywords filter lets some through, so the
        # profile's exclusions are enforced here as well.
        if banned and any(b in _haystack(job) for b in banned):
            continue

        if expanded:
            if not any(k in _haystack(job) for k in expanded):
                continue
        elif apply_stack_filters:
            text = _haystack(job)
            if not any(k in text for k in jobs_config.STACK_KEYWORDS):
                continue

            strong_dev = any(k in text for k in jobs_config.STRONG_DEV_KEYWORDS)
            platform_locked = any(k in text for k in jobs_config.EXCLUDE_ROLE_HINTS)
            if platform_locked and not strong_dev:
                continue

            title = str(job.get("title") or "").lower()
            if any(term in title for term in jobs_config.EXCLUDE_TITLE_TERMS):
                continue

        out.append(job)
    return out
