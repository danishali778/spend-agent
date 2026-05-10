from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories import cases as case_repository
from app.repositories import decisions as decision_repository
from app.repositories import artifacts as artifact_repository
from app.repositories import runs as run_repository
from app.repositories import supabase_rest
from app.schemas.api import CaseSummary, DecisionResponse, GetActivityResponse, GetArtifactsResponse, GetCaseResponse, ListCasesResponse
from app.schemas.api import CreateCaseInput
from app.services.cache_service import CacheService


class CaseService:
    def __init__(self, cache_service: CacheService | None = None) -> None:
        self.cache_service = cache_service or CacheService()
        try:
            self.rest_client = supabase_rest.SupabaseRestClient.from_env()
        except Exception:  # noqa: BLE001
            self.rest_client = None

    def list_cases(self, session: Session | None):
        cached = self.cache_service.client.get_json(self.cache_service.case_list_key())
        if cached is not None:
            return ListCasesResponse.model_validate(cached)
        if session is None:
            if self.rest_client is None:
                raise ValueError("Database URL is not configured.")
            items = supabase_rest.list_cases(self.rest_client)
        else:
            items = case_repository.list_cases(session)
        response = ListCasesResponse(items=items, nextCursor=None)
        self.cache_service.client.set_json(self.cache_service.case_list_key(), response.model_dump(), self.cache_service.case_list_ttl())
        return response

    def create_case(self, session: Session | None, input_data: CreateCaseInput):
        normalized_value = input_data.renewalDate.replace("Z", "+00:00") if input_data.renewalDate else None
        if session is None:
            if self.rest_client is None:
                raise ValueError("Database URL is not configured.")
            result = supabase_rest.create_case(
                self.rest_client,
                vendor_name=input_data.vendorName,
                owner_user_id=input_data.ownerUserId,
                renewal_date=normalized_value,
            )
        else:
            renewal_date = datetime.fromisoformat(normalized_value) if normalized_value else None
            result = case_repository.create_case(session, vendor_name=input_data.vendorName, owner_user_id=input_data.ownerUserId, renewal_date=renewal_date)
        self.cache_service.invalidate_case(result.id)
        return result

    def get_case_detail(self, session: Session | None, case_id: str):
        cached = self.cache_service.client.get_json(self.cache_service.case_detail_key(case_id))
        if cached is not None:
            return GetCaseResponse.model_validate(cached)
        if session is None:
            if self.rest_client is None:
                raise ValueError("Database URL is not configured.")
            response = supabase_rest.get_case_detail(self.rest_client, case_id)
        else:
            response = case_repository.get_case_detail(session, case_id)
        if response is not None:
            self.cache_service.client.set_json(self.cache_service.case_detail_key(case_id), response.model_dump(), self.cache_service.case_detail_ttl())
        return response

    def get_latest_decision(self, session: Session | None, case_id: str) -> DecisionResponse | None:
        cached = self.cache_service.client.get_json(self.cache_service.decision_key(case_id))
        if cached is not None:
            return DecisionResponse.model_validate(cached)
        latest_run_id = None
        if session is None:
            if self.rest_client is None:
                raise ValueError("Database URL is not configured.")
            latest_run = supabase_rest.get_latest_run(self.rest_client, case_id)
            latest_run_id = str(latest_run["id"]) if latest_run else None
            response = supabase_rest.get_latest_decision(self.rest_client, case_id, run_id=latest_run_id)
        else:
            latest_run = run_repository.get_latest_run(session, case_id)
            latest_run_id = latest_run.id if latest_run is not None else None
            response = decision_repository.get_latest_decision(session, case_id, run_id=latest_run_id)
        if response is not None:
            self.cache_service.client.set_json(self.cache_service.decision_key(case_id), response.model_dump(), self.cache_service.decision_ttl())
        return response

    def get_artifacts(self, session: Session | None, case_id: str) -> GetArtifactsResponse | None:
        cached = self.cache_service.client.get_json(self.cache_service.artifacts_key(case_id))
        if cached is not None:
            return GetArtifactsResponse.model_validate(cached)
        latest_run_id = None
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
        if items is None:
            return None
        response = GetArtifactsResponse(items=items)
        self.cache_service.client.set_json(self.cache_service.artifacts_key(case_id), response.model_dump(), self.cache_service.artifacts_ttl())
        return response

    def get_activity(self, session: Session | None, case_id: str) -> GetActivityResponse | None:
        cached = self.cache_service.client.get_json(self.cache_service.activity_key(case_id))
        if cached is not None:
            return GetActivityResponse.model_validate(cached)
        if session is None:
            if self.rest_client is None:
                raise ValueError("Database URL is not configured.")
            response = supabase_rest.get_activity_response(self.rest_client, case_id=case_id)
        else:
            latest_run_id = None
            latest_run = run_repository.get_latest_run(session, case_id)
            if latest_run is not None:
                latest_run_id = latest_run.id
            response = run_repository.get_activity_response(session, case_id=case_id, run_id=latest_run_id)
        if response is not None:
            self.cache_service.client.set_json(self.cache_service.activity_key(case_id), response.model_dump(), self.cache_service.activity_ttl())
        return response
