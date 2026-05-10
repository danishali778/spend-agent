from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_case_service, get_db
from app.schemas.api import DecisionResponse, GetActivityResponse, GetArtifactsResponse
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases/{case_id}", tags=["activity"])


@router.get("/decision", response_model=DecisionResponse)
def get_latest_decision(
    case_id: str,
    session: Session | None = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
) -> DecisionResponse:
    response = case_service.get_latest_decision(session, case_id)
    if response is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Decision not found"})
    return response


@router.get("/artifacts", response_model=GetArtifactsResponse)
def get_artifacts(
    case_id: str,
    session: Session | None = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
) -> GetArtifactsResponse:
    response = case_service.get_artifacts(session, case_id)
    if response is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Artifacts not found"})
    return response


@router.get("/activity", response_model=GetActivityResponse)
def get_activity(
    case_id: str,
    session: Session | None = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
) -> GetActivityResponse:
    response = case_service.get_activity(session, case_id)
    if response is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Activity not found"})
    return response
