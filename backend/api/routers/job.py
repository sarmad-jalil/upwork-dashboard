from fastapi import APIRouter, HTTPException, Depends
from api.core.dependencies import get_api_key
from api.models.schemas import JobEvaluateRequest, JobEvaluateResponse
from api.services.job_service import evaluate_job

router = APIRouter(prefix="/job", tags=["Job"])


@router.post("/evaluate", response_model=JobEvaluateResponse)
def evaluate_job_endpoint(req: JobEvaluateRequest, api_key: str | None = Depends(get_api_key)):
    try:
        return evaluate_job(req, api_key=api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
