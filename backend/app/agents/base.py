from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Mapping, TypeVar

from app.services.provider_client import ProviderClient

T = TypeVar("T")


class AgentSchemaError(ValueError):
    pass


@dataclass(frozen=True)
class AgentInvocation:
    prompt_name: str
    payload: Dict[str, Any]


class BaseSpecialistAgent(Generic[T]):
    agent_name: str
    prompt_name: str

    def __init__(self, provider_client: ProviderClient, parser: Callable[[Mapping[str, Any]], T]) -> None:
        self.provider_client = provider_client
        self._parser = parser

    def build_payload(self, state: Mapping[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def parse_result(self, payload: Mapping[str, Any]) -> T:
        try:
            return self._parser(dict(payload))
        except Exception as exc:
            raise AgentSchemaError(f"{self.agent_name} returned invalid payload: {exc}") from exc

    def validate_result(self, result: T, payload: Mapping[str, Any]) -> None:
        return None

    def run(self, state: Mapping[str, Any]) -> T:
        payload = self.build_payload(state)
        raw = self.provider_client.generate_json(agent_name=self.agent_name, prompt_name=self.prompt_name, payload=payload)
        result = self.parse_result(raw)
        try:
            self.validate_result(result, payload)
        except Exception as exc:
            raise AgentSchemaError(f"{self.agent_name} returned invalid payload: {exc}") from exc
        return result
