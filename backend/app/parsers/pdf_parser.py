from __future__ import annotations

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.schemas.domain import PageText, PdfExtractionResult


def _normalize_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.replace("\r", "").split("\n")]
    return "\n".join(line for line in lines if line).strip()


def extract_pdf_text(
    document_id: str,
    storage_path: str | None = None,
    *,
    raw_text: str | None = None,
    raw_bytes: bytes | None = None,
) -> PdfExtractionResult:
    if raw_text is None and raw_bytes is None and storage_path is None:
        return PdfExtractionResult(
            status="error",
            text="",
            error_code="missing_input",
            message=f"No source content provided for document {document_id}.",
        )

    if raw_text is not None:
        page_chunks = [_normalize_text(chunk) for chunk in raw_text.split("\f")]
    else:
        path = Path(storage_path or "")
        pdf_bytes = raw_bytes
        if pdf_bytes is None:
            if not path.exists():
                return PdfExtractionResult(
                    status="error",
                    text="",
                    error_code="file_not_found",
                    message=f"Storage path not found for document {document_id}: {storage_path}",
                )
            pdf_bytes = path.read_bytes()

        try:
            reader = PdfReader(BytesIO(pdf_bytes))
        except Exception as exc:  # noqa: BLE001
            return PdfExtractionResult(
                status="error",
                text="",
                error_code="invalid_pdf",
                message=f"Unable to parse PDF for document {document_id}: {exc}",
            )

        page_chunks = []
        for page in reader.pages:
            try:
                extracted = page.extract_text() or ""
            except Exception:
                extracted = ""
            page_chunks.append(_normalize_text(extracted))

    pages = [
        PageText(page_number=index + 1, text=chunk)
        for index, chunk in enumerate(page_chunks)
        if chunk
    ]

    if not pages:
        return PdfExtractionResult(
            status="error",
            text="",
            error_code="empty_document",
            message=f"No readable text found for document {document_id}.",
        )

    return PdfExtractionResult(status="ok", text="\n".join(page.text for page in pages), pages=pages)
