# SpendAgent Backend

Python-first backend for SpendAgent using:

- FastAPI for HTTP routes
- Celery for background analysis runs
- Redis for broker, result backend, and short-lived cache
- Supabase Postgres and Storage as the system of record

## Local Run

1. Create a Python environment and install `backend[dev]`.
2. Set environment variables from [`backend/.env.example`](./.env.example).
3. Run all backend commands from `backend/.venv`.
4. Choose provider mode:
   - `SPENDAGENT_PROVIDER_MODE=mock` for deterministic local development
   - `SPENDAGENT_PROVIDER_MODE=groq` for live Groq-backed `DecisionAgent` and `CommsAgent`
   - `SPENDAGENT_PROVIDER_MODE=gemini` for live Gemini-backed `DecisionAgent` and `CommsAgent`
5. If using Groq mode, set:
   - `GROQ_API_KEY`
   - `SPENDAGENT_GROQ_MODEL`
6. If using Gemini mode, set:
   - `GEMINI_API_KEY`
   - `SPENDAGENT_GEMINI_MODEL`
7. Start the API:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

8. Start the Celery worker on Windows:

```powershell
celery -A app.core.celery_app.celery_app worker --pool=solo --loglevel=info
```

9. Point the frontend to `http://localhost:8000/api/v1`.

## Notes

- The backend preserves the existing HTTP contract used by `frontend/`.
- `frontend/` is the only web app location in the repo.
- Redis failures are treated as soft failures for cache reads/writes, but Celery still requires a working Redis broker.
- In `groq` mode, provider errors or invalid JSON fail the run; the backend does not silently fall back to mock reasoning.
- In `gemini` mode, provider errors or invalid JSON also fail the run; switch models/providers by env instead of code changes.
