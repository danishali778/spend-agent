from __future__ import annotations

from app.core.cache import CacheClient


class CacheService:
    def __init__(self, client: CacheClient | None = None) -> None:
        self.client = client or CacheClient()

    def case_list_key(self) -> str:
        return "cases:list"

    def case_detail_key(self, case_id: str) -> str:
        return f"cases:{case_id}:detail"

    def decision_key(self, case_id: str) -> str:
        return f"cases:{case_id}:decision"

    def artifacts_key(self, case_id: str) -> str:
        return f"cases:{case_id}:artifacts"

    def activity_key(self, case_id: str, run_id: str | None = None) -> str:
        return f"cases:{case_id}:activity:{run_id or 'latest'}"

    def case_list_ttl(self) -> int:
        return 15

    def case_detail_ttl(self) -> int:
        return 15

    def decision_ttl(self) -> int:
        return 15

    def artifacts_ttl(self) -> int:
        return 15

    def activity_ttl(self) -> int:
        return 3

    def invalidate_case(self, case_id: str) -> None:
        self.client.delete_many(self.case_list_key(), self.case_detail_key(case_id), self.decision_key(case_id), self.artifacts_key(case_id), self.activity_key(case_id), f"analysis-lock:{case_id}")
