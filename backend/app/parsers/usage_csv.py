from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from app.schemas.domain import UsageNormalizationResult, UsageRow, UsageSummary

TRUE_VALUES = {"true", "1", "yes", "y", "active"}
FALSE_VALUES = {"false", "0", "no", "n", "inactive"}


def _parse_active(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValueError(f"Unsupported active flag: {value}")


def _pick_value(row: dict[str, str], *keys: str) -> str:
    lowered = {key.lower(): value for key, value in row.items()}
    for key in keys:
        if key.lower() in lowered and lowered[key.lower()].strip():
            return lowered[key.lower()].strip()
    raise KeyError(f"Missing required CSV column. Expected one of: {', '.join(keys)}")


def parse_csv_usage(document_id: str, storage_path: str | None = None, *, raw_text: str | None = None) -> UsageNormalizationResult:
    if raw_text is None and storage_path is None:
        return UsageNormalizationResult(status="error", error_code="missing_input", message=f"No CSV content provided for document {document_id}.")
    try:
        content = raw_text if raw_text is not None else Path(storage_path or "").read_text(encoding="utf-8")
    except FileNotFoundError:
        return UsageNormalizationResult(status="error", error_code="file_not_found", message=f"CSV storage path not found for document {document_id}: {storage_path}")

    try:
        reader = csv.DictReader(StringIO(content))
        rows: list[UsageRow] = []
        for raw_row in reader:
            if not raw_row:
                continue
            user_id = _pick_value(raw_row, "userId", "user_id", "email")
            active = _parse_active(_pick_value(raw_row, "active", "isActive", "enabled"))
            last_seen_at = None
            for key in ("lastSeenAt", "last_seen_at", "last_login_at"):
                value = raw_row.get(key) or raw_row.get(key.lower())
                if value and value.strip():
                    last_seen_at = value.strip()
                    break
            rows.append(UsageRow(user_id=user_id, active=active, last_seen_at=last_seen_at, raw={key: value for key, value in raw_row.items() if key is not None}))
    except (KeyError, ValueError, csv.Error) as exc:
        return UsageNormalizationResult(status="error", error_code="invalid_csv", message=f"Could not normalize usage CSV for document {document_id}: {exc}")

    active_users = sum(1 for row in rows if row.active)
    return UsageNormalizationResult(
        status="ok",
        rows=rows,
        summary=UsageSummary(active_users=active_users, total_rows=len(rows), inactive_users=len(rows) - active_users),
    )
