from fastapi import APIRouter, HTTPException, Query

from api.models.schemas import JobsScrapeResponse
from api.services.apify_client import ApifyError, scrape_jobs_raw
from api.services.jobs_filter import filter_relevant
from api.services.jobs_scraper import collect_for_profile
from api.services.profile_store_service import get_profile
from api.services.jobs_store_service import save_scraped_jobs, list_saved_jobs, oldest_saved_posted

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/scrape", response_model=JobsScrapeResponse)
def scrape_jobs_endpoint(
    since: str | None = Query(None, description="ISO date; only jobs posted on/after this date"),
    limit: int | None = Query(None, ge=1, le=200, description="Max jobs to request from Apify per page"),
    profile_id: int | None = Query(None, description="Scrape using this profile's niche/keywords instead of the global default stack"),
    deep: bool = Query(True, description="Walk the window backwards to reach jobs beyond the first page"),
):
    # No profile: legacy whole-stack sweep, single page.
    if profile_id is None:
        try:
            raw = scrape_jobs_raw(since_iso=since, limit=limit)
        except ApifyError as e:
            raise HTTPException(status_code=502, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Job scraping failed: {str(e)}")
        filtered = filter_relevant(raw, apply_stack_filters=True)
        return JobsScrapeResponse(
            jobs=filtered,
            total_scraped=len(raw),
            total_after_filter=len(filtered),
            new_count=len(filtered),
        )

    try:
        profile = get_profile(profile_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Continue the backwards walk from the oldest job already stored, so a
    # refresh explores unseen ground instead of re-billing the same slice.
    start_before = oldest_saved_posted(profile_id) if deep else None

    try:
        matched, total_raw, pages = collect_for_profile(
            profile,
            limit=limit,
            start_before=start_before,
            max_pages=None if deep else 1,
        )
    except ApifyError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job scraping failed: {str(e)}")

    known = {j.id for j in list_saved_jobs(profile_id)}
    response_batch = JobsScrapeResponse(
        jobs=matched, total_scraped=total_raw, total_after_filter=len(matched)
    ).jobs
    new_count = sum(1 for j in response_batch if j.id not in known)

    save_scraped_jobs(profile_id, response_batch)
    saved = list_saved_jobs(profile_id)

    return JobsScrapeResponse(
        jobs=saved,
        total_scraped=total_raw,
        total_after_filter=len(saved),
        new_count=new_count,
        pages_scanned=pages,
    )
