from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = "SpendAgent Backend"
    api_v1_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = ""
    redis_url: str = "redis://localhost:6379/0"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    demo_owner_id: str = "00000000-0000-0000-0000-000000000001"
    prompt_bundle_version: str = "v1.0.0"
    provider_mode: str = "mock"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout_seconds: float = 30.0
    groq_temperature: float = 0.1
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_seconds: float = 30.0
    gemini_temperature: float = 0.1
    cache_enabled: bool = True

    @property
    def celery_result_backend(self) -> str:
        return self.redis_url

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL", "")
        return cls(
            host=os.environ.get("BACKEND_HOST", "0.0.0.0"),
            port=int(os.environ.get("BACKEND_PORT", os.environ.get("PORT", "8000"))),
            database_url=database_url,
            redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
            supabase_url=(
                os.environ.get("SUPABASE_URL")
                or os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
            ).rstrip("/"),
            supabase_service_role_key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
            demo_owner_id=os.environ.get("SPENDAGENT_DEMO_OWNER_ID", "00000000-0000-0000-0000-000000000001"),
            prompt_bundle_version=os.environ.get("SPENDAGENT_PROMPT_BUNDLE_VERSION", "v1.0.0"),
            provider_mode=os.environ.get("SPENDAGENT_PROVIDER_MODE", "mock"),
            groq_api_key=os.environ.get("GROQ_API_KEY", ""),
            groq_model=os.environ.get("SPENDAGENT_GROQ_MODEL", "llama-3.3-70b-versatile"),
            groq_timeout_seconds=float(os.environ.get("SPENDAGENT_GROQ_TIMEOUT_SECONDS", "30")),
            groq_temperature=float(os.environ.get("SPENDAGENT_GROQ_TEMPERATURE", "0.1")),
            gemini_api_key=os.environ.get("GEMINI_API_KEY", ""),
            gemini_model=os.environ.get("SPENDAGENT_GEMINI_MODEL", "gemini-2.5-flash"),
            gemini_timeout_seconds=float(os.environ.get("SPENDAGENT_GEMINI_TIMEOUT_SECONDS", "30")),
            gemini_temperature=float(os.environ.get("SPENDAGENT_GEMINI_TEMPERATURE", "0.1")),
            cache_enabled=os.environ.get("SPENDAGENT_CACHE_ENABLED", "true").lower() != "false",
        )


settings = Settings.from_env()
