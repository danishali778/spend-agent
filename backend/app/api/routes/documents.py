from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.api.deps import get_db, get_document_service
from app.repositories import cases as case_repository
from app.repositories import supabase_rest
from app.schemas.api import DocumentSummary, UploadEmailInput
from app.services.document_service import DocumentService

router = APIRouter(prefix="/cases/{case_id}/documents", tags=["documents"])

FILE_TYPES = {"contract_pdf", "invoice_pdf", "usage_csv"}


def _ensure_case_exists(session: Session | None, case_id: str) -> None:
    if session is None:
        client = supabase_rest.SupabaseRestClient.from_env()
        row = supabase_rest.get_case_row(client, case_id)
    else:
        row = case_repository.get_case_row(session, case_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Case not found"})


@router.post("")
async def upload_document(
    case_id: str,
    request: Request,
    session: Session | None = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),
) -> dict[str, DocumentSummary]:
    _ensure_case_exists(session, case_id)
    content_type = (request.headers.get("content-type") or "").lower()

    if "application/json" in content_type:
        payload = UploadEmailInput.model_validate(await request.json())
        document = document_service.upload_email(session, case_id, payload)
        return {"document": document}

    if "multipart/form-data" in content_type:
        form = await request.form()
        document_type = str(form.get("type") or "").strip()
        if document_type not in FILE_TYPES:
            raise HTTPException(status_code=400, detail={"code": "invalid_document_type", "message": "Document type must be contract_pdf, invoice_pdf, or usage_csv"})

        upload = form.get("file")
        if not isinstance(upload, UploadFile):
            raise HTTPException(status_code=400, detail={"code": "file_required", "message": "A file upload is required"})

        source_name = str(form.get("sourceName") or "").strip() or upload.filename or f"{document_type}-upload"
        payload = await upload.read()
        if not payload:
            raise HTTPException(status_code=400, detail={"code": "empty_file", "message": "Uploaded file is empty"})

        document = document_service.upload_file(
            session,
            case_id,
            document_type=document_type,
            source_name=source_name,
            file_bytes=payload,
            content_type=upload.content_type or "application/octet-stream",
        )
        return {"document": document}

    raise HTTPException(status_code=415, detail={"code": "unsupported_media_type", "message": "Use JSON for renewal_email or multipart/form-data for file uploads"})
