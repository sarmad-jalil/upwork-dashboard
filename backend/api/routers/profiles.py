from fastapi import APIRouter, HTTPException

from api.models.schemas import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    ProfileResponse,
    ProfileListResponse,
    JobsScrapeResponse,
)
from api.services.profile_store_service import (
    list_profiles,
    create_profile,
    update_profile,
    delete_profile,
    activate_profile,
    get_profile,
)
from api.services.jobs_store_service import list_saved_jobs

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("", response_model=ProfileListResponse)
def list_profiles_endpoint():
    return ProfileListResponse(profiles=list_profiles())


@router.post("", response_model=ProfileResponse)
def create_profile_endpoint(req: ProfileCreateRequest):
    return create_profile(req)


@router.patch("/{profile_id}", response_model=ProfileResponse)
def update_profile_endpoint(profile_id: int, req: ProfileUpdateRequest):
    try:
        return update_profile(profile_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{profile_id}")
def delete_profile_endpoint(profile_id: int):
    try:
        delete_profile(profile_id)
        return {"deleted": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{profile_id}/activate", response_model=ProfileResponse)
def activate_profile_endpoint(profile_id: int):
    try:
        return activate_profile(profile_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{profile_id}/jobs", response_model=JobsScrapeResponse)
def profile_jobs_history_endpoint(profile_id: int):
    try:
        get_profile(profile_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    jobs = list_saved_jobs(profile_id)
    return JobsScrapeResponse(jobs=jobs, total_scraped=len(jobs), total_after_filter=len(jobs))
