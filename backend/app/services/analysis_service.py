from __future__ import annotations

from dataclasses import dataclass
import logging
from threading import Thread
from typing import Any

from celery import signature
from kombu.exceptions import OperationalError
from sqlalchemy.orm import Session

from app.core.cache import CacheClient
from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories import artifacts as artifact_repository
from app.orchestrator.run_manager import AgentRunManager
from app.repositories import cases as case_repository
from app.repositories import decisions as decision_repository
from app.repositories import documents as document_repository
from app.repositories import runs as run_repository
from app.repositories import supabase_rest
from app.schemas.api import AnalyzeCaseResponse, DecisionResponse, GetActivityResponse, GetArtifactsResponse
from app.schemas.domain import CaseRecord, DocumentRecord, DocumentType, RecommendedAction
from app.services.cache_service import CacheService
from app.services.provider_client import create_provider_client
from app.storage.supabase_storage import SupabaseStorageClient
from app.parsers.pdf_parser import extract_pdf_text


@dataclass
class LoadedCaseBundle:
    case: CaseRecord
    documents: list[DocumentRecord]


class AnalysisService:
    def __init__(self, cache_service: CacheService | None = None, storage_client: SupabaseStorageClient | None = None) -> None:
        self.cache_service = cache_service or CacheService()
        self.storage_client = storage_client or SupabaseStorageClient()
        self.provider_client = create_provider_client(settings)
        try:
            self.rest_client = supabase_rest.SupabaseRestClient.from_env()
        except Exception:  # noqa: BLE001
            self.rest_client = None

    def enqueue_case_analysis(self, session: Session | None, case_id: str, *, force_reanalyze: bool = False) -> AnalyzeCaseResponse:
        if session is None:
            if self.rest_client is None:
                raise ValueError("Database URL is not configured.")
            existing_run = supabase_rest.get_latest_run(self.rest_client, case_id)
            if existing_run and not force_reanalyze and str(existing_run["status"]) in {"queued", "running"}:
                if str(existing_run["status"]) == "queued":
                    self._dispatch(str(existing_run["id"]), case_id)
                return AnalyzeCaseResponse(runId=str(existing_run["id"]), status=str(existing_run["status"]))
            response = supabase_rest.create_run(
                self.rest_client,
                case_id=case_id,
                triggered_by_user_id=settings.demo_owner_id,
                prompt_bundle_version=settings.prompt_bundle_version,
            )
            supabase_rest.update_case_status(self.rest_client, case_id, status="analyzing")
        else:
            existing_run = run_repository.get_latest_run(session, case_id)
            if existing_run and not force_reanalyze and existing_run.status in {"queued", "running"}:
                if existing_run.status == "queued":
                    self._dispatch(existing_run.id, case_id)
                return AnalyzeCaseResponse(runId=existing_run.id, status=existing_run.status)

            response = run_repository.create_run(session, case_id=case_id, triggered_by_user_id=settings.demo_owner_id, prompt_bundle_version=settings.prompt_bundle_version)
            case_repository.update_case_status(session, case_id, status="analyzing")
        self.cache_service.invalidate_case(case_id)
        self._dispatch(response.runId, case_id)
        return response

    def _dispatch(self, run_id: str, case_id: str) -> None:
        try:
            signature("app.tasks.analysis.analyze_case_run", kwargs={"run_id": run_id, "case_id": case_id}, task_id=run_id).apply_async()
        except OperationalError:
            logging.getLogger("spendagent.backend").warning(
                "Celery broker unavailable; falling back to in-process background execution for run %s",
                run_id,
            )
            Thread(target=self._run_analysis_inline, args=(run_id, case_id), daemon=True).start()

    def _run_analysis_inline(self, run_id: str, case_id: str) -> None:
        session = SessionLocal() if SessionLocal else None
        try:
            self.execute_case_analysis(session, run_id, case_id)
        except Exception:  # noqa: BLE001
            logging.getLogger("spendagent.backend").exception("Inline analysis fallback failed for run %s", run_id)
        finally:
            if session is not None:
                session.close()

    def execute_case_analysis(self, session: Session | None, run_id: str, case_id: str) -> dict[str, Any]:
        cache_client = CacheClient()
        lock_key = f"analysis-lock:{case_id}"
        if not cache_client.acquire_lock(lock_key, ttl_seconds=300):
            return {"status": "locked"}
        try:
            bundle = self.load_case_bundle(session, case_id)
            if session is None:
                if self.rest_client is None:
                    raise ValueError("Database URL is not configured.")
                persistence = supabase_rest.SupabaseRestPersistenceHook(self.rest_client, case_id=case_id, run_id=run_id)
            else:
                persistence = run_repository.SqlAlchemyPersistenceHook(session, case_id=case_id, run_id=run_id)
            manager = AgentRunManager(provider_client=self.provider_client, persistence_hook=persistence)
            result = manager.execute(bundle.case, bundle.documents, run_id=run_id)
            self.cache_service.invalidate_case(case_id)
            return result.persisted_state
        finally:
            cache_client.release_lock(lock_key)

    def load_case_bundle(self, session: Session | None, case_id: str) -> LoadedCaseBundle:
        if session is None:
            if self.rest_client is None:
                raise ValueError("Database URL is not configured.")
            return supabase_rest.load_case_bundle(case_id, self.rest_client)

        case_detail = case_repository.get_case_detail(session, case_id)
        if case_detail is None:
            raise ValueError(f"Case {case_id} not found")
        case_row = case_repository.get_case_row(session, case_id)
        if case_row is None:
            raise ValueError(f"Case {case_id} not found")
        documents = document_repository.list_document_rows_for_case(session, case_id)
        mapped_documents: list[DocumentRecord] = []
        for document in documents:
            raw_text = document.raw_text
            parse_status = document.parse_status
            if document.storage_path and (raw_text is None or ("pdf" in document.type and parse_status != "parsed")):
                bucket, object_path = document.storage_path.split("/", 1)
                payload = self.storage_client.download_bytes(bucket, object_path)
                if "pdf" in (document.mime_type or "").lower():
                    extraction = extract_pdf_text(document.id, raw_bytes=payload)
                    raw_text = extraction.text if extraction.status == "ok" else None
                    parse_status = "parsed" if extraction.status == "ok" else "failed"
                else:
                    raw_text = payload.decode("utf-8", errors="ignore")
                    parse_status = "parsed"
                document_repository.update_document_parse_result(session, document.id, raw_text=raw_text, parse_status=parse_status)
            mapped_documents.append(DocumentRecord(id=document.id, case_id=document.case_id, type=DocumentType(document.type), source_name=document.source_name, raw_text=raw_text, parse_status=parse_status, storage_path=document.storage_path, mime_type=document.mime_type))

        return LoadedCaseBundle(
            case=CaseRecord(
                id=case_row.id,
                vendor_name=case_row.vendor_name,
                owner_user_id=case_row.owner_user_id,
                status=case_row.status,
                renewal_date=case_row.renewal_date.isoformat() if case_row.renewal_date else None,
                urgency_level=case_row.urgency_level,
                projected_savings=float(case_row.projected_savings) if case_row.projected_savings is not None else None,
                projected_savings_status=case_row.projected_savings_status,
                recommended_action=RecommendedAction(case_row.recommended_action) if case_row.recommended_action else None,
            ),
            documents=mapped_documents,
        )

    def get_latest_decision(self, session: Session | None, case_id: str) -> DecisionResponse | None:
        if session is None:
            if self.rest_client is None:
                raise ValueError("Database URL is not configured.")
            latest_run = supabase_rest.get_latest_run(self.rest_client, case_id)
            latest_run_id = str(latest_run["id"]) if latest_run else None
            return supabase_rest.get_latest_decision(self.rest_client, case_id, run_id=latest_run_id)
        latest_run = run_repository.get_latest_run(session, case_id)
        latest_run_id = latest_run.id if latest_run is not None else None
        return decision_repository.get_latest_decision(session, case_id, run_id=latest_run_id)

    def get_artifacts(self, session: Session | None, case_id: str) -> GetArtifactsResponse | None:
        if session is None:
            if self.rest_client is None:
                raise ValueError("Database URL is not configured.")
            latest_run = supabase_rest.get_latest_run(self.rest_client, case_id)
            latest_run_id = str(latest_run["id"]) if latest_run else None
            items = supabase_rest.get_artifacts(self.rest_client, case_id, run_id=latest_run_id)
        else:
            latest_run = run_repository.get_latest_run(session, case_id)
            latest_run_id = latest_run.id if latest_run is not None else None
            items = artifact_repository.get_artifacts(session, case_id, run_id=latest_run_id)
        return None if items is None else GetArtifactsResponse(items=items)

    def get_activity(self, session: Session | None, case_id: str) -> GetActivityResponse | None:
        if session is None:
            if self.rest_client is None:
                raise ValueError("Database URL is not configured.")
            return supabase_rest.get_activity_response(self.rest_client, case_id=case_id)
        return run_repository.get_activity_response(session, case_id=case_id)
