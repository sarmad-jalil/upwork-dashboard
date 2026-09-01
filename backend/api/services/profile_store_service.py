from psycopg2.extras import Json

from api.core.db import get_conn
from api.models.schemas import ProfileCreateRequest, ProfileUpdateRequest, ProfileResponse

# Columns an update is allowed to touch. Bounds the identifiers interpolated
# into the UPDATE below (is_active is excluded on purpose — see activate_profile).
UPDATABLE_FIELDS = {
    "name", "niche", "keywords", "exclude_keywords", "experience", "model", "min_job_score",
}


def _row_to_profile(row: dict) -> ProfileResponse:
    return ProfileResponse(
        id=row["id"],
        name=row["name"],
        niche=row["niche"],
        keywords=row["keywords"],
        exclude_keywords=row["exclude_keywords"],
        experience=row["experience"],
        model=row["model"],
        min_job_score=row["min_job_score"],
        is_active=row["is_active"],
        created_at=row["created_at"].isoformat(),
    )


def list_profiles() -> list[ProfileResponse]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM profiles ORDER BY created_at ASC")
            rows = cur.fetchall()
    return [_row_to_profile(r) for r in rows]


def get_profile(profile_id: int) -> ProfileResponse:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM profiles WHERE id = %s", (profile_id,))
            row = cur.fetchone()
    if row is None:
        raise ValueError(f"Profile {profile_id} not found")
    return _row_to_profile(row)


def create_profile(req: ProfileCreateRequest) -> ProfileResponse:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM profiles")
            existing = cur.fetchone()["c"]
            cur.execute(
                """
                INSERT INTO profiles (name, niche, keywords, exclude_keywords, experience, model, min_job_score, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    req.name,
                    req.niche,
                    Json(req.keywords),
                    Json(req.exclude_keywords),
                    req.experience,
                    req.model.value,
                    req.min_job_score,
                    existing == 0,  # first profile created becomes active
                ),
            )
            row = cur.fetchone()
    return _row_to_profile(row)


def update_profile(profile_id: int, req: ProfileUpdateRequest) -> ProfileResponse:
    # exclude_unset so an omitted field keeps its current value rather than
    # being overwritten with None.
    data = {k: v for k, v in req.model_dump(exclude_unset=True).items() if k in UPDATABLE_FIELDS}
    if not data:
        return get_profile(profile_id)

    assignments, values = [], []
    for field, value in data.items():
        if field in ("keywords", "exclude_keywords"):
            value = Json(value or [])
        elif field == "model":
            value = getattr(value, "value", value)
        assignments.append(f"{field} = %s")
        values.append(value)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE profiles SET {', '.join(assignments)} WHERE id = %s RETURNING *",
                (*values, profile_id),
            )
            row = cur.fetchone()

    if row is None:
        raise ValueError(f"Profile {profile_id} not found")
    return _row_to_profile(row)


def delete_profile(profile_id: int) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT is_active FROM profiles WHERE id = %s", (profile_id,))
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"Profile {profile_id} not found")
            was_active = row["is_active"]
            cur.execute("DELETE FROM profiles WHERE id = %s", (profile_id,))
            if was_active:
                cur.execute("SELECT id FROM profiles ORDER BY created_at ASC LIMIT 1")
                next_row = cur.fetchone()
                if next_row is not None:
                    cur.execute("UPDATE profiles SET is_active = TRUE WHERE id = %s", (next_row["id"],))


def activate_profile(profile_id: int) -> ProfileResponse:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM profiles WHERE id = %s", (profile_id,))
            if cur.fetchone() is None:
                raise ValueError(f"Profile {profile_id} not found")
            cur.execute("UPDATE profiles SET is_active = FALSE")
            cur.execute("UPDATE profiles SET is_active = TRUE WHERE id = %s RETURNING *", (profile_id,))
            row = cur.fetchone()
    return _row_to_profile(row)
