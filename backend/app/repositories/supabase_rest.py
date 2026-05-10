from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib import parse, request
from uuid import uuid4

from app.core.config import settings
from app.parsers.pdf_parser import extract_pdf_text
from app.schemas.api import (
    AgentActivityEventResponse,
    AnalyzeCaseResponse,
    CaseDetail,
    CaseSummary,
    DecisionBlocker,
    DecisionEvidenceItem,
    DecisionPacketResponse,
    DecisionResponse,
    DocumentSummary,
    GeneratedArtifactResponse,
    GetActivityResponse,
    GetCaseResponse,
)
from app.schemas.domain import (
    AgentActivityEvent,
    ArtifactType,
    CaseRecord,
    CommsAgentResult,
    DecisionPacket,
    DocumentAnalysisResult,
    DocumentRecord,
    FactProvenanceKind,
    DocumentType,
    FinanceAnalysisResult,
    PolicyEvaluationResult,
    ProjectedSavingsStatus,
    RecommendedAction,
    RunFailureCategory,
)


class SupabaseApiError(RuntimeError):
    pass


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class LoadedCaseBundle:
    case: CaseRecord
    documents: list[DocumentRecord]


@dataclass
class SupabaseRestClient:
    base_url: str
    service_role_key: str

    @classmethod
    def from_env(cls) -> "SupabaseRestClient":
        base_url = settings.supabase_url or (
            os.environ.get("SUPABASE_URL")
            or os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
        ).rstrip("/")
        service_role_key = settings.supabase_service_role_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not base_url or not service_role_key:
            raise SupabaseApiError("Supabase URL or service role key is missing from environment")
        return cls(base_url=base_url, service_role_key=service_role_key)

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        payload: Any = None,
        headers: dict[str, str] | None = None,
        return_raw: bool = False,
    ) -> Any:
        query = f"?{parse.urlencode(params)}" if params else ""
        url = f"{self.base_url}{path}{query}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = request.Request(url, data=data, method=method, headers=self._headers(headers))
        try:
            with request.urlopen(req) as response:
                body = response.read()
                if return_raw:
                    return body
                if not body:
                    return None
                return json.loads(body.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise SupabaseApiError(f"Supabase request failed: {method} {path} {exc}") from exc

    def select(
        self,
        table: str,
        *,
        columns: str = "*",
        filters: dict[str, str] | None = None,
        order: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        params = {"select": columns}
        if filters:
            params.update(filters)
        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = str(limit)
        result = self._request("GET", f"/rest/v1/{table}", params=params)
        return result or []

    def insert(self, table: str, rows: Iterable[dict[str, Any]], *, prefer: str = "return=representation") -> list[dict[str, Any]]:
        return self._request("POST", f"/rest/v1/{table}", payload=list(rows), headers={"Prefer": prefer}) or []

    def insert_one(self, table: str, row: dict[str, Any], *, prefer: str = "return=representation") -> dict[str, Any] | None:
        rows = self.insert(table, [row], prefer=prefer)
        return rows[0] if rows else None

    def update(self, table: str, row: dict[str, Any], *, filters: dict[str, str], prefer: str = "return=representation") -> list[dict[str, Any]]:
        return self._request("PATCH", f"/rest/v1/{table}", params=filters, payload=row, headers={"Prefer": prefer}) or []

    def download_storage_object(self, bucket: str, object_path: str) -> bytes:
        encoded_path = "/".join(parse.quote(part) for part in object_path.split("/"))
        return self._request("GET", f"/storage/v1/object/authenticated/{bucket}/{encoded_path}", return_raw=True)


def _iso_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def case_summary_from_row(row: dict[str, Any]) -> CaseSummary:
    return CaseSummary(
        id=str(row["id"]),
        vendorName=str(row["vendor_name"]),
        status=str(row["status"]),
        renewalDate=_iso_string(row.get("renewal_date")),
        urgencyLevel=_iso_string(row.get("urgency_level")),
        projectedSavings=float(row["projected_savings"]) if row.get("projected_savings") is not None else None,
        projectedSavingsStatus=str(row.get("projected_savings_status") or ("calculated" if row.get("projected_savings") is not None else "not_available")),
        recommendedAction=_iso_string(row.get("recommended_action")),
    )


def document_summary_from_row(row: dict[str, Any]) -> DocumentSummary:
    return DocumentSummary(
        id=str(row["id"]),
        type=str(row["type"]),
        sourceName=str(row["source_name"]),
        parseStatus=str(row["parse_status"]),
    )


def list_cases(client: SupabaseRestClient) -> list[CaseSummary]:
    rows = client.select("cases", order="created_at.desc")
    return [case_summary_from_row(row) for row in rows]


def create_case(
    client: SupabaseRestClient,
    *,
    vendor_name: str,
    owner_user_id: str,
    renewal_date: str | None,
) -> CaseSummary:
    payload = {
        "id": str(uuid4()),
        "vendor_name": vendor_name,
        "owner_user_id": owner_user_id,
        "status": "draft",
        "renewal_date": renewal_date,
    }
    row = client.insert_one("cases", payload)
    if row is None:
        raise SupabaseApiError("Failed to create case")
    return case_summary_from_row(row)


def get_case_row(client: SupabaseRestClient, case_id: str) -> dict[str, Any] | None:
    rows = client.select("cases", filters={"id": f"eq.{case_id}"}, limit=1)
    return rows[0] if rows else None


def get_latest_run(client: SupabaseRestClient, case_id: str) -> dict[str, Any] | None:
    rows = client.select("agent_runs", filters={"case_id": f"eq.{case_id}"}, order="created_at.desc", limit=1)
    return rows[0] if rows else None


def get_case_detail(client: SupabaseRestClient, case_id: str) -> GetCaseResponse | None:
    row = get_case_row(client, case_id)
    if row is None:
        return None
    documents = client.select("documents", filters={"case_id": f"eq.{case_id}"}, order="uploaded_at.asc")
    latest_run = get_latest_run(client, case_id)
    summary = case_summary_from_row(row)
    return GetCaseResponse(
        case=CaseDetail(
            **summary.model_dump(),
            ownerUserId=str(row["owner_user_id"]),
            notes=row.get("notes"),
            createdAt=str(row.get("created_at") or ""),
            updatedAt=str(row.get("updated_at") or ""),
        ),
        documents=[document_summary_from_row(document) for document in documents],
        latestRunId=str(latest_run["id"]) if latest_run else None,
        latestRunStatus=str(latest_run["status"]) if latest_run else None,
        latestRunFailureReason=_iso_string(latest_run.get("failure_reason")) if latest_run else None,
        latestRunFailureCategory=_iso_string(latest_run.get("failure_category")) if latest_run else None,
    )


def update_case_status(
    client: SupabaseRestClient,
    case_id: str,
    *,
    status: str,
    projected_savings: float | None = None,
    projected_savings_status: str = "not_available",
    recommended_action: str | None = None,
    urgency_level: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "status": status,
        "projected_savings": projected_savings,
        "projected_savings_status": projected_savings_status,
        "recommended_action": recommended_action,
        "updated_at": utc_timestamp(),
    }
    if urgency_level is not None:
        payload["urgency_level"] = urgency_level
    client.update("cases", payload, filters={"id": f"eq.{case_id}"})


def create_document(
    client: SupabaseRestClient,
    *,
    case_id: str,
    type: str,
    source_name: str,
    storage_path: str | None,
    raw_text: str | None,
    mime_type: str | None,
    parse_status: str,
) -> DocumentSummary:
    row = client.insert_one(
        "documents",
        {
            "id": str(uuid4()),
            "case_id": case_id,
            "type": type,
            "source_name": source_name,
            "storage_path": storage_path,
            "raw_text": raw_text,
            "mime_type": mime_type,
            "parse_status": parse_status,
        },
    )
    if row is None:
        raise SupabaseApiError("Failed to create document")
    return document_summary_from_row(row)


def list_document_rows_for_case(client: SupabaseRestClient, case_id: str) -> list[dict[str, Any]]:
    return client.select("documents", filters={"case_id": f"eq.{case_id}"}, order="uploaded_at.asc")


def update_document_parse_result(client: SupabaseRestClient, document_id: str, *, raw_text: str | None, parse_status: str) -> None:
    client.update("documents", {"raw_text": raw_text, "parse_status": parse_status}, filters={"id": f"eq.{document_id}"})


def create_run(client: SupabaseRestClient, *, case_id: str, triggered_by_user_id: str, prompt_bundle_version: str) -> AnalyzeCaseResponse:
    row = client.insert_one(
        "agent_runs",
        {
            "id": str(uuid4()),
            "case_id": case_id,
            "status": "queued",
            "triggered_by_user_id": triggered_by_user_id,
            "prompt_bundle_version": prompt_bundle_version,
        },
    )
    if row is None:
        raise SupabaseApiError("Failed to create run")
    return AnalyzeCaseResponse(runId=str(row["id"]), status=str(row["status"]))


def mark_run_started(client: SupabaseRestClient, run_id: str) -> None:
    client.update(
        "agent_runs",
        {"status": "running", "started_at": utc_timestamp(), "failure_reason": None, "failure_category": None},
        filters={"id": f"eq.{run_id}"},
    )


def finish_run(
    client: SupabaseRestClient,
    run_id: str,
    *,
    status: str,
    failure_reason: str | None = None,
    failure_category: str | None = None,
) -> None:
    client.update(
        "agent_runs",
        {
            "status": status,
            "completed_at": utc_timestamp(),
            "failure_reason": failure_reason,
            "failure_category": failure_category,
        },
        filters={"id": f"eq.{run_id}"},
    )


def get_latest_decision(client: SupabaseRestClient, case_id: str, *, run_id: str | None = None) -> DecisionResponse | None:
    filters = {"case_id": f"eq.{case_id}"}
    if run_id is not None:
        filters["run_id"] = f"eq.{run_id}"
    rows = client.select("decisions", filters=filters, order="decision_version.desc", limit=1)
    if not rows:
        return None
    row = rows[0]
    documents = {
        str(document["id"]): str(document["source_name"])
        for document in client.select("documents", columns="id,source_name", filters={"case_id": f"eq.{case_id}"})
    }
    evidence = [
        DecisionEvidenceItem(
            factKey=str(item.get("factKey", "unknown")),
            value=item.get("value"),
            documentId=str(item.get("documentId") or item.get("sourceDocumentId", "unknown")),
            sourceName=documents.get(str(item.get("documentId") or item.get("sourceDocumentId", "unknown"))),
            snippet=str(item.get("snippet") or item.get("sourceSnippet", "")),
            confidenceScore=float(item.get("confidenceScore") or item.get("confidence_score") or 0),
            provenanceKind=item.get("provenanceKind"),
        )
        for item in (row.get("evidence_json") or [])
    ]
    blockers = [
        DecisionBlocker(
            code=(f"blocker_{index + 1}" if isinstance(item, str) else str(item.get("code", f"blocker_{index + 1}"))),
            message=(str(item) if isinstance(item, str) else str(item.get("message", "Unknown blocker"))),
        )
        for index, item in enumerate(row.get("blockers_json") or [])
    ]
    return DecisionResponse(
        decisionVersion=int(row["decision_version"]),
        decision=DecisionPacketResponse(
            recommendedAction=str(row["recommended_action"]),
            confidenceScore=float(row["confidence_score"]),
            rationale=str(row["rationale"]),
            evidence=evidence,
            projectedSavings=float(row["projected_savings"]) if row.get("projected_savings") is not None else None,
            projectedSavingsStatus=str(row.get("projected_savings_status") or ("calculated" if row.get("projected_savings") is not None else "not_available")),
            blockers=blockers,
            nextStep=str(row["next_step"]),
            fallbackAction=_iso_string(row.get("fallback_action")),
        ),
    )


def get_artifacts(client: SupabaseRestClient, case_id: str, *, run_id: str | None = None) -> list[GeneratedArtifactResponse] | None:
    filters = {"case_id": f"eq.{case_id}"}
    if run_id is not None:
        filters["run_id"] = f"eq.{run_id}"
    decision_rows = client.select("decisions", filters=filters, order="decision_version.desc", limit=1)
    if not decision_rows:
        return None
    decision = decision_rows[0]
    rows = client.select("generated_artifacts", filters={"decision_id": f"eq.{decision['id']}"}, order="created_at.asc")
    return [
        GeneratedArtifactResponse(
            artifactType=str(row["artifact_type"]),
            title=str(row["title"]),
            content=str(row["content"]),
            decisionVersion=int(decision["decision_version"]),
            createdAt=_iso_string(row.get("created_at")),
        )
        for row in rows
    ]


def get_activity_response(client: SupabaseRestClient, case_id: str, *, run_id: str | None = None) -> GetActivityResponse | None:
    run = None
    if run_id:
        rows = client.select("agent_runs", filters={"id": f"eq.{run_id}"}, limit=1)
        run = rows[0] if rows else None
    else:
        run = get_latest_run(client, case_id)
    if run is None:
        return None
    steps = client.select("agent_steps", filters={"run_id": f"eq.{run['id']}"}, order="started_at.asc")
    return GetActivityResponse(
        runId=str(run["id"]),
        status=str(run["status"]),
        events=[
            AgentActivityEventResponse(
                runId=str(step["run_id"]),
                agentName=str(step["agent_name"]),
                stepName=str(step["step_name"]),
                status=str(step["status"]),
                startedAt=_iso_string(step.get("started_at")),
                completedAt=_iso_string(step.get("completed_at")),
                summary=str(step.get("summary") or ""),
                error=step.get("error_json"),
            )
            for step in steps
        ],
        failureReason=_iso_string(run.get("failure_reason")),
        failureCategory=_iso_string(run.get("failure_category")),
    )


def load_case_bundle(case_id: str, client: SupabaseRestClient) -> LoadedCaseBundle:
    case_row = get_case_row(client, case_id)
    if case_row is None:
        raise ValueError(f"Case {case_id} not found")

    document_rows = list_document_rows_for_case(client, case_id)
    documents: list[DocumentRecord] = []
    for row in document_rows:
        raw_text = row.get("raw_text")
        parse_status = str(row.get("parse_status") or "pending")
        storage_path = row.get("storage_path")
        document_type = str(row["type"])
        should_reparse = bool(storage_path and (raw_text is None or ("pdf" in document_type and parse_status != "parsed")))
        if should_reparse and storage_path and "/" in str(storage_path):
            bucket, object_path = str(storage_path).split("/", 1)
            payload = client.download_storage_object(bucket, object_path)
            if "pdf" in str(row.get("mime_type") or "").lower():
                extraction = extract_pdf_text(str(row["id"]), raw_bytes=payload)
                raw_text = extraction.text if extraction.status == "ok" else None
                parse_status = "parsed" if extraction.status == "ok" else "failed"
            else:
                raw_text = payload.decode("utf-8", errors="ignore")
                parse_status = "parsed"
            update_document_parse_result(client, str(row["id"]), raw_text=raw_text, parse_status=parse_status)

        documents.append(
            DocumentRecord(
                id=str(row["id"]),
                case_id=str(row["case_id"]),
                type=DocumentType(document_type),
                source_name=str(row["source_name"]),
                raw_text=raw_text if isinstance(raw_text, str) else None,
                parse_status=parse_status,
                storage_path=str(storage_path) if storage_path else None,
                mime_type=str(row["mime_type"]) if row.get("mime_type") else None,
            )
        )

    row_action = case_row.get("recommended_action")
    return LoadedCaseBundle(
        case=CaseRecord(
            id=str(case_row["id"]),
            vendor_name=str(case_row["vendor_name"]),
            owner_user_id=str(case_row["owner_user_id"]),
            status=str(case_row["status"]),
            renewal_date=_iso_string(case_row.get("renewal_date")),
            urgency_level=_iso_string(case_row.get("urgency_level")),
            projected_savings=float(case_row["projected_savings"]) if case_row.get("projected_savings") is not None else None,
            projected_savings_status=ProjectedSavingsStatus(str(case_row.get("projected_savings_status") or ("calculated" if case_row.get("projected_savings") is not None else "not_available"))),
            recommended_action=RecommendedAction(str(row_action)) if row_action else None,
        ),
        documents=documents,
    )


@dataclass
class SupabaseRestPersistenceHook:
    client: SupabaseRestClient
    run_id: str
    case_id: str
    step_row_ids: dict[str, str] = field(default_factory=dict)
    latest_decision_id: str | None = None
    latest_decision_version: int | None = None
    failure_reason: str | None = None
    failure_category: RunFailureCategory | None = None

    def start_run(self, run_id: str, case, prompt_bundle_version: str) -> None:
        self.run_id = run_id
        self.case_id = case.id
        mark_run_started(self.client, run_id)

    def record_step(
        self,
        run_id: str,
        agent_name: str,
        step_name: str,
        status: str,
        retry_count: int,
        summary: str | None,
        error: dict[str, Any] | None = None,
    ) -> None:
        key = f"{agent_name}:{step_name}"
        if status == "running":
            row = self.client.insert_one(
                "agent_steps",
                {
                    "run_id": run_id,
                    "agent_name": agent_name,
                    "step_name": step_name,
                    "status": status,
                    "summary": summary,
                    "started_at": utc_timestamp(),
                    "retry_count": retry_count,
                    "error_json": error,
                },
            )
            if row:
                self.step_row_ids[key] = str(row["id"])
            return

        row_id = self.step_row_ids.get(key)
        payload = {
            "status": status,
            "summary": summary,
            "completed_at": utc_timestamp(),
            "retry_count": retry_count,
            "error_json": error,
        }
        if row_id:
            self.client.update("agent_steps", payload, filters={"id": f"eq.{row_id}"})
        else:
            self.client.insert(
                "agent_steps",
                [{
                    "run_id": run_id,
                    "agent_name": agent_name,
                    "step_name": step_name,
                    "status": status,
                    "summary": summary,
                    "started_at": utc_timestamp(),
                    "completed_at": utc_timestamp(),
                    "retry_count": retry_count,
                    "error_json": error,
                }],
            )

    def persist_document_result(self, run_id: str, result: DocumentAnalysisResult) -> None:
        rows = [
            {
                "id": str(uuid4()),
                "case_id": self.case_id,
                "document_id": fact.source_document_id,
                "fact_key": fact.fact_key,
                "fact_value_json": fact.value,
                "source_snippet": fact.source_snippet,
                "source_page": None,
                "confidence_score": fact.confidence_score,
                "provenance_kind": fact.provenance_kind.value,
                "provenance_note": fact.provenance_note,
                "extracted_by_run_id": run_id,
            }
            for fact in result.facts
        ]
        if rows:
            self.client.insert("extracted_facts", rows)

    def persist_finance_result(self, run_id: str, result: FinanceAnalysisResult) -> None:
        snapshot = result.usage_snapshot
        self.client.insert(
            "usage_snapshots",
            [{
                "id": str(uuid4()),
                "case_id": self.case_id,
                "seats_purchased": snapshot.seats_purchased,
                "seats_active": snapshot.seats_active,
                "utilization_percent": snapshot.utilization_percent,
                "cost_period": snapshot.cost_period,
                "total_cost": snapshot.total_cost,
                "currency": snapshot.currency,
                "snapshot_source": "merged",
                "created_by_run_id": run_id,
            }],
        )

    def persist_policy_results(self, run_id: str, result: PolicyEvaluationResult) -> None:
        rows = [
            {
                "id": str(uuid4()),
                "case_id": self.case_id,
                "run_id": run_id,
                "proposed_action": "escalate" if result.requires_escalation else "renegotiate",
                "threshold_name": check.threshold_name,
                "result": check.result,
                "message": check.message,
            }
            for check in result.checks
        ]
        if rows:
            self.client.insert("policy_checks", rows)

    def persist_decision(self, run_id: str, decision: DecisionPacket) -> None:
        latest = self.client.select("decisions", columns="decision_version", filters={"case_id": f"eq.{self.case_id}"}, order="decision_version.desc", limit=1)
        decision_version = int(latest[0]["decision_version"]) + 1 if latest else 1
        row = self.client.insert_one(
            "decisions",
            {
                "id": str(uuid4()),
                "case_id": self.case_id,
                "run_id": run_id,
                "decision_version": decision_version,
                "recommended_action": decision.recommended_action.value,
                "fallback_action": decision.fallback_action.value if decision.fallback_action else None,
                "confidence_score": decision.confidence_score,
                "rationale": decision.rationale,
                "projected_savings": decision.projected_savings,
                "projected_savings_status": decision.projected_savings_status.value,
                "blockers_json": decision.blockers,
                "next_step": decision.next_step,
                "evidence_json": [item.to_state_dict() for item in decision.evidence],
            },
        )
        if row:
            self.latest_decision_id = str(row["id"])
            self.latest_decision_version = int(row["decision_version"])

    def persist_artifacts(self, run_id: str, artifacts: CommsAgentResult) -> None:
        if not self.latest_decision_id:
            return
        rows = [
            {
                "id": str(uuid4()),
                "case_id": self.case_id,
                "decision_id": self.latest_decision_id,
                "artifact_type": artifact.artifact_type.value if isinstance(artifact.artifact_type, ArtifactType) else str(artifact.artifact_type),
                "title": artifact.title,
                "content": artifact.content,
            }
            for artifact in artifacts.artifacts
        ]
        if rows:
            self.client.insert("generated_artifacts", rows)

    def finish_run(self, run_id: str, status: str) -> None:
        finish_run(
            self.client,
            run_id,
            status=status,
            failure_reason=self.failure_reason,
            failure_category=self.failure_category.value if self.failure_category else None,
        )

    def update_case_summary(self, *, status: str, projected_savings: float | None, projected_savings_status: str, recommended_action: str | None, urgency_level: str | None = None) -> None:
        update_case_status(
            self.client,
            self.case_id,
            status=status,
            projected_savings=projected_savings,
            projected_savings_status=projected_savings_status,
            recommended_action=recommended_action,
            urgency_level=urgency_level,
        )

    def get_activity(self, run_id: str) -> list[AgentActivityEvent]:
        response = get_activity_response(self.client, self.case_id, run_id=run_id)
        if response is None:
            return []
        return [
            AgentActivityEvent(
                run_id=event.runId,
                agent_name=event.agentName,
                step_name=event.stepName,
                status=event.status,
                started_at=event.startedAt,
                completed_at=event.completedAt,
                summary=event.summary,
            )
            for event in response.events
        ]

    def snapshot(self, run_id: str) -> dict[str, Any]:
        response = get_activity_response(self.client, self.case_id, run_id=run_id)
        return {
            "status": response.status if response else "unknown",
            "activity": [event.model_dump() for event in response.events] if response else [],
            "decisionId": self.latest_decision_id,
            "decisionVersion": self.latest_decision_version,
        }
