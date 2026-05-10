from __future__ import annotations

from email import policy
from email.parser import Parser

from app.extractors.date_money_extractor import extract_iso_dates
from app.schemas.domain import EmailFieldsResult


def extract_email_fields(document_id: str, email_text: str) -> EmailFieldsResult:
    if not email_text.strip():
        return EmailFieldsResult(
            status="error",
            subject=None,
            sender=None,
            body="",
            error_code="empty_email",
            message=f"Email content is empty for document {document_id}.",
        )

    parsed = Parser(policy=policy.default).parsestr(email_text)
    body = parsed.get_body(preferencelist=("plain",))
    normalized_body = body.get_content() if body is not None else parsed.get_payload()
    if not isinstance(normalized_body, str):
        normalized_body = str(normalized_body)

    return EmailFieldsResult(
        status="ok",
        subject=parsed.get("Subject"),
        sender=parsed.get("From"),
        body=normalized_body.strip(),
        detected_dates=extract_iso_dates(normalized_body),
    )
