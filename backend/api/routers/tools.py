from fastapi import APIRouter, HTTPException, Depends
from api.core.dependencies import get_api_key
from api.models.schemas import (
    TitleGenerateRequest,
    TitleGenerateResponse,
    ConversionCoachRequest,
    ConversionCoachResponse,
)
from api.services.title_service import generate_titles
from api.services.conversion_service import conversion_coach

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.post("/generate-titles", response_model=TitleGenerateResponse)
def generate_titles_endpoint(req: TitleGenerateRequest, api_key: str | None = Depends(get_api_key)):
    try:
        return generate_titles(req, api_key=api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Title generation failed: {str(e)}")


@router.post("/conversion-coach", response_model=ConversionCoachResponse)
def conversion_coach_endpoint(req: ConversionCoachRequest, api_key: str | None = Depends(get_api_key)):
    try:
        return conversion_coach(req, api_key=api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion coaching failed: {str(e)}")
