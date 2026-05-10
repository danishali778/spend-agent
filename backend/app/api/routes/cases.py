from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_case_service, get_db
from app.schemas.api import CreateCaseInput, CreateCaseResponse, GetCaseResponse, ListCasesResponse
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=ListCasesResponse)
def list_cases(
    session: Session | None = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
) -> ListCasesResponse:
    return case_service.list_cases(session)


@router.post("", response_model=CreateCaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CreateCaseInput,
    session: Session | None = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
) -> CreateCaseResponse:
    case_summary = case_service.create_case(session, payload)
    return CreateCaseResponse(case=case_summary)


@router.get("/{case_id}", response_model=GetCaseResponse)
def get_case_detail(
    case_id: str,
    session: Session | None = Depends(get_db),
    case_service: CaseService = Depends(get_case_service),
) -> GetCaseResponse:
    response = case_service.get_case_detail(session, case_id)
    if response is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Case not found"})
    return response
