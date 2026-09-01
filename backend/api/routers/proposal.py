from fastapi import APIRouter, HTTPException, Depends
from api.core.dependencies import get_api_key
from api.models.schemas import ProposalGenerateRequest, ProposalGenerateResponse
from api.services.proposal_service import generate_proposal

router = APIRouter(prefix="/proposal", tags=["Proposal"])


@router.post("/generate", response_model=ProposalGenerateResponse)
def generate_proposal_endpoint(req: ProposalGenerateRequest, api_key: str | None = Depends(get_api_key)):
    try:
        return generate_proposal(req, api_key=api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proposal generation failed: {str(e)}")
