from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from app.parsers.pdf_parser import extract_pdf_text
from app.repositories import documents as document_repository
from app.repositories import supabase_rest
from app.schemas.api import UploadEmailInput
from app.services.cache_service import CacheService
from app.storage.supabase_storage import SupabaseStorageClient


def bucket_for_document_type(document_type: str) -> str:
    return {
        "contract_pdf": "contracts",
        "invoice_pdf": "invoices",
        "usage_csv": "usage-exports",
    }[document_type]


class DocumentService:
    def __init__(self, storage_client: SupabaseStorageClient | None = None, cache_service: CacheService | None = None) -> None:
        self.storage_client = storage_client or SupabaseStorageClient()
        self.cache_service = cache_service or CacheService()
        try:
            self.rest_client = supabase_rest.SupabaseRestClient.from_env()
        except Exception:  # noqa: BLE001
            self.rest_client = None

    def upload_email(self, session: Session | None, case_id: str, payload: UploadEmailInput):
        if session is None:
            if self.rest_client is None:
                raise ValueError("Database URL is not configured.")
            result = supabase_rest.create_document(
                self.rest_client,
                case_id=case_id,
                type="renewal_email",
                source_name=payload.sourceName,
                storage_path=None,
                raw_text=payload.emailText,
                mime_type="message/rfc822",
                parse_status="parsed",
            )
        else:
            result = document_repository.create_document(
                session,
                case_id=case_id,
                type="renewal_email",
                source_name=payload.sourceName,
                storage_path=None,
                raw_text=payload.emailText,
                mime_type="message/rfc822",
                parse_status="parsed",
            )
        self.cache_service.invalidate_case(case_id)
        return result

    def upload_file(self, session: Session | None, case_id: str, *, document_type: str, source_name: str, file_bytes: bytes, content_type: str):
        bucket = bucket_for_document_type(document_type)
        object_path = f"{case_id}/{uuid4()}-{source_name}"
        self.storage_client.upload_bytes(bucket, object_path, file_bytes, content_type)
        storage_path = f"{bucket}/{object_path}"

        raw_text = None
        parse_status = "pending"
        if document_type == "usage_csv":
            raw_text = file_bytes.decode("utf-8", errors="ignore")
            parse_status = "parsed"
        elif document_type in {"contract_pdf", "invoice_pdf"}:
            extraction = extract_pdf_text(str(uuid4()), raw_bytes=file_bytes)
            if extraction.status == "ok":
                raw_text = extraction.text
                parse_status = "parsed"
            else:
                parse_status = "failed"

        if session is None:
            if self.rest_client is None:
                raise ValueError("Database URL is not configured.")
            result = supabase_rest.create_document(
                self.rest_client,
                case_id=case_id,
                type=document_type,
                source_name=source_name,
                storage_path=storage_path,
                raw_text=raw_text,
                mime_type=content_type,
                parse_status=parse_status,
            )
        else:
            result = document_repository.create_document(
                session,
                case_id=case_id,
                type=document_type,
                source_name=source_name,
                storage_path=storage_path,
                raw_text=raw_text,
                mime_type=content_type,
                parse_status=parse_status,
            )
        self.cache_service.invalidate_case(case_id)
        return result
