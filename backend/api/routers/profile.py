from fastapi import APIRouter, HTTPException, Depends
from api.core.dependencies import get_api_key
from api.models.schemas import ProfileAnalyzeRequest, ProfileAnalyzeResponse
from api.services.profile_service import analyze_profile

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post("/analyze", response_model=ProfileAnalyzeResponse)
def analyze_profile_endpoint(req: ProfileAnalyzeRequest, api_key: str | None = Depends(get_api_key)):
    try:
        return analyze_profile(req, api_key=api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
