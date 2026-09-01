"""Collects jobs for a profile across several time windows.

The actor returns one stable slice per query — an unchanged query gives back the
exact same jobs every time, and `clientId`/`notifications_only` only surface the
handful posted since the last call. Since results are capped at `limit` per call
but the 24h pool is much larger, the way to reach the rest is to walk the window
backwards: each page asks for jobs older than the oldest one seen so far.
"""
from api.core import jobs_config
from api.services.apify_client import scrape_jobs_raw
from api.services.jobs_filter import filter_relevant


def _oldest_posted(jobs: list[dict]) -> str | None:
    dates = [j.get("date_posted") for j in jobs if j.get("date_posted")]
    return min(dates) if dates else None


def collect_for_profile(
    profile,
    limit: int | None = None,
    start_before: str | None = None,
    max_pages: int | None = None,
    target_new: int | None = None,
) -> tuple[list[dict], int, int]:
    """Returns (matching_jobs, total_raw_seen, pages_used).

    `start_before` continues a backwards walk from a previous run (pass the
    oldest job already stored) so a refresh explores new ground instead of
    re-billing the slice it already has.
    """
    max_pages = max_pages or jobs_config.MAX_PAGES
    target_new = target_new or jobs_config.TARGET_NEW_JOBS

    exclude_keywords = ", ".join(profile.exclude_keywords) if profile.exclude_keywords else None
    match_keywords = profile.keywords or None

    matched: list[dict] = []
    seen_ids: set[str] = set()
    total_raw = 0
    cursor = start_before  # None => start at the newest window
    pages = 0

    for page in range(max_pages):
        # First page of a fresh walk uses the default recent window so newly
        # posted jobs are always picked up; later pages step further back.
        since_iso = None
        date_override = f"<={cursor}" if cursor else None

        batch = scrape_jobs_raw(
            since_iso=since_iso,
            limit=limit,
            exclude_keywords=exclude_keywords,
            min_job_score=profile.min_job_score,
            date_posted=date_override,
        )
        pages = page + 1
        total_raw += len(batch)
        if not batch:
            break

        fresh = [j for j in batch if str(j.get("id")) not in seen_ids]
        if not fresh:
            break
        seen_ids.update(str(j.get("id")) for j in fresh)

        matched.extend(
            filter_relevant(
                fresh,
                apply_stack_filters=False,
                match_keywords=match_keywords,
                exclude_keywords=profile.exclude_keywords or None,
            )
        )
        if len(matched) >= target_new:
            break

        oldest = _oldest_posted(batch)
        if not oldest or oldest == cursor:
            break  # window stopped moving — nothing deeper to reach
        cursor = oldest

    return matched, total_raw, pages
