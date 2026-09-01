from psycopg2.extras import execute_values, Json

from api.core.db import get_conn
from api.models.schemas import JobListing

MAX_JOBS_PER_PROFILE = 50

_COLUMNS = [
    "job_id", "title", "url", "description", "skills",
    "category_name", "subcategory_name", "price_type", "price", "price_min", "price_max",
    "experience_level", "client_location", "buyer_payment_verified", "buyer_score",
    "hire_rate", "total_spent", "date_posted", "job_score",
    # Kept because the proposal writer needs them: client strength, and the
    # application instructions clients use to filter copy-paste applicants.
    "open_jobs", "avg_hourly_rate", "questions",
    "ai_specific_requirements_before_applying", "ai_anti_bot_phrase",
]


def _job_values(job: JobListing) -> tuple:
    return (
        job.id, job.title, job.url, job.description, job.skills,
        job.category_name, job.subcategory_name, job.price_type, job.price, job.price_min, job.price_max,
        job.experience_level, job.client_location, job.buyer_payment_verified, job.buyer_score,
        job.hire_rate, job.total_spent, job.date_posted, job.job_score,
        job.open_jobs, job.avg_hourly_rate,
        Json(job.questions) if job.questions else None,
        job.ai_specific_requirements_before_applying, job.ai_anti_bot_phrase,
    )


def save_scraped_jobs(profile_id: int, jobs: list[JobListing]) -> None:
    """Upserts jobs for this profile, then trims to the most-recently-scraped
    MAX_JOBS_PER_PROFILE rows so history doesn't grow unbounded."""
    jobs = [j for j in jobs if j.id]
    if not jobs:
        return

    col_list = ", ".join(_COLUMNS)
    update_list = ", ".join(f"{c} = EXCLUDED.{c}" for c in _COLUMNS if c != "job_id")
    # One statement for the whole batch — a row-at-a-time loop meant one network
    # round trip per job, which dominated scrape time against a remote database.
    template = "(%s, " + ", ".join(["%s"] * len(_COLUMNS)) + ", now())"
    rows = [(profile_id, *_job_values(job)) for job in jobs]

    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur,
                f"""
                INSERT INTO jobs (profile_id, {col_list}, scraped_at)
                VALUES %s
                ON CONFLICT (profile_id, job_id) DO UPDATE SET {update_list}, scraped_at = now()
                """,
                rows,
                template=template,
            )
            cur.execute(
                """
                DELETE FROM jobs
                WHERE profile_id = %s
                AND job_id NOT IN (
                    SELECT job_id FROM jobs WHERE profile_id = %s ORDER BY scraped_at DESC LIMIT %s
                )
                """,
                (profile_id, profile_id, MAX_JOBS_PER_PROFILE),
            )


def oldest_saved_posted(profile_id: int) -> str | None:
    """Oldest `date_posted` stored for this profile — the anchor a refresh
    continues its backwards walk from."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT min(date_posted) AS oldest FROM jobs WHERE profile_id = %s",
                (profile_id,),
            )
            row = cur.fetchone()
    oldest = row["oldest"] if row else None
    return oldest.isoformat() if oldest else None


def list_saved_jobs(profile_id: int) -> list[JobListing]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM jobs WHERE profile_id = %s ORDER BY scraped_at DESC",
                (profile_id,),
            )
            rows = cur.fetchall()

    out = []
    for row in rows:
        data = dict(row)
        data["id"] = data.pop("job_id")
        data.pop("profile_id", None)
        data.pop("scraped_at", None)
        if data.get("date_posted") is not None:
            data["date_posted"] = data["date_posted"].isoformat()
        out.append(JobListing(**data))
    return out
