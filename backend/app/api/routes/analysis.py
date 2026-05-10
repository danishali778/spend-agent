from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_analysis_service, get_db
from app.repositories import cases as case_repository
from app.repositories import supabase_rest
from app.schemas.api import AnalyzeCaseInput, AnalyzeCaseResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/cases/{case_id}/analyze", tags=["analysis"])


@router.post("", response_model=AnalyzeCaseResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_case_analysis(
    case_id: str,
    request: Request,
    session: Session | None = Depends(get_db),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalyzeCaseResponse:
    if session is None:
        client = supabase_rest.SupabaseRestClient.from_env()
        case_row = supabase_rest.get_case_row(client, case_id)
    else:
        case_row = case_repository.get_case_row(session, case_id)
    if case_row is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Case not found"})
    raw_body = await request.body()
    payload = AnalyzeCaseInput.model_validate_json(raw_body) if raw_body else AnalyzeCaseInput()
    return analysis_service.enqueue_case_analysis(session, case_id, force_reanalyze=bool(payload.forceReanalyze))
