import httpx

from api.core import jobs_config
from api.core.config import get_settings


class ApifyError(RuntimeError):
    pass


def scrape_jobs_raw(
    since_iso: str | None = None,
    limit: int | None = None,
    keywords: str | None = None,
    skills: str | None = None,
    exclude_keywords: str | None = None,
    min_job_score: int | None = None,
    date_posted: str | None = None,
) -> list[dict]:
    settings = get_settings()
    token = settings.apify_token
    if not token:
        raise ApifyError("APIFY_TOKEN is not set")

    payload = dict(jobs_config.DEFAULT_SCRAPE_INPUT)
    if since_iso:
        payload["date_posted"] = f">={since_iso}"
    if limit:
        payload["limit"] = limit
    if keywords:
        payload["keywords"] = keywords
    if skills:
        payload["skills"] = skills
    if exclude_keywords:
        payload["exclude_keywords"] = exclude_keywords
    if min_job_score is not None:
        payload["job_score"] = f">={min_job_score}"
    # Explicit window override ("<=<iso>") used to page backwards through the
    # pool. Takes precedence over the default recent window.
    if date_posted:
        payload["date_posted"] = date_posted

    actor_path = jobs_config.SCRAPER_ACTOR.replace("/", "~")
    url = f"https://api.apify.com/v2/acts/{actor_path}/run-sync-get-dataset-items"

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, params={"token": token}, json=payload)

    if resp.status_code >= 400:
        raise ApifyError(f"Apify run failed ({resp.status_code}): {resp.text[:500]}")

    items = resp.json()
    return items if isinstance(items, list) else []
