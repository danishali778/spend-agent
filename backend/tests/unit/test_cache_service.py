from __future__ import annotations

from app.services.cache_service import CacheService


class FakeCacheClient:
    def __init__(self) -> None:
        self.deleted: list[str] = []

    def delete_many(self, *keys: str) -> None:
        self.deleted.extend(keys)


def test_cache_service_keys_and_invalidation() -> None:
    client = FakeCacheClient()
    service = CacheService(client=client)

    assert service.case_list_key() == "cases:list"
    assert service.case_detail_key("case-1") == "cases:case-1:detail"
    assert service.decision_key("case-1") == "cases:case-1:decision"
    assert service.artifacts_key("case-1") == "cases:case-1:artifacts"
    assert service.activity_key("case-1") == "cases:case-1:activity:latest"
    assert service.activity_ttl() == 3
    assert service.case_list_ttl() == 15

    service.invalidate_case("case-1")

    assert "cases:list" in client.deleted
    assert "cases:case-1:detail" in client.deleted
    assert "cases:case-1:decision" in client.deleted
    assert "cases:case-1:artifacts" in client.deleted
    assert "cases:case-1:activity:latest" in client.deleted
    assert "analysis-lock:case-1" in client.deleted
