# SpendAgent

SpendAgent is a multi-agent procurement renewal workbench. It helps finance and procurement teams review SaaS renewals using contract data, invoice data, usage data, and renewal email signals, then produces a recommended action and the supporting artifacts needed to act on it.

## The problem

Software renewals are usually handled across disconnected systems:

- contracts contain renewal terms and notice windows
- invoices contain spend signals
- usage exports show whether the license footprint still makes sense
- renewal emails define the actual timing pressure

By the time someone manually pieces those inputs together, the negotiation window is often gone. The result is over-licensed renewals, missed downgrade opportunities, and weak vendor leverage.

## What SpendAgent does

SpendAgent turns a renewal into a structured case. For each case it can:

1. ingest contract, invoice, usage, and renewal-email inputs
2. extract and normalize evidence
3. evaluate utilization, savings opportunity, and policy constraints
4. recommend an action:
   - `renew`
   - `downgrade`
   - `cancel`
   - `renegotiate`
   - `escalate`
5. generate follow-up artifacts such as:
   - CFO summary
   - internal approval note
   - vendor negotiation draft

The workflow is autonomous inside the analysis pipeline, but still designed for human review before external action.

## Product shape

The current product is a monorepo with:

- a `Next.js` frontend in `frontend/`
- a `FastAPI + Celery` backend in `backend/`
- shared TypeScript contracts in `packages/`
- `Supabase Postgres` and `Supabase Storage` as backend infrastructure
- `Redis` for Celery and cache support

The frontend is built as a procurement workbench rather than a chatbot. The primary workflow is:

`Evidence -> Analysis -> Recommendation -> Artifacts`

## Current features

### Frontend

- work-queue dashboard for active renewal cases
- responsive application shell
- case creation flow
- case detail workflow with:
  - evidence intake
  - uploaded document list
  - run state and activity timeline
  - recommendation summary
  - supporting evidence with provenance
  - savings explanation
  - generated artifact tabs

### Backend

- FastAPI routes for cases, documents, analysis, decisions, artifacts, and activity
- Celery-backed analysis workflow
- agent-based orchestration for:
  - document analysis
  - finance analysis
  - policy checks
  - decision generation
  - communications artifact generation
- mock provider mode for deterministic local development
- live provider support via Groq or Gemini for agent output generation

### Shared packages

- `@spendagent/shared-types` for API and domain contracts
- `@spendagent/ui-contracts` for frontend view-model contracts
- prompt and decision-rule packages used by the backend and shared logic

## Repository layout

```text
.
├── backend/           FastAPI, Celery, parsing, orchestration, tests
├── frontend/          Next.js application
├── packages/          Shared TS packages and contracts
├── supabase/          SQL migrations and seed data
├── pyproject.toml     Root pytest configuration
└── package.json       Workspace configuration
```

## Local development

Use the Linux-native checkout if you are on Ubuntu:

```bash
~/Projects/P27
```

Do not run the frontend from an NTFS-mounted copy if you can avoid it. Native packages such as `esbuild` are more reliable from the Linux home directory.

### Prerequisites

- Python 3.11+
- Node 20.x
- npm
- Redis
- Supabase project credentials

### 1. Backend setup

```bash
cd ~/Projects/P27/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
```

Set the required values in `backend/.env`.

Important variables:

- `SUPABASE_DB_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `REDIS_URL`
- `SPENDAGENT_PROVIDER_MODE`

Provider modes:

- `mock` for deterministic local development
- `groq` for live provider-backed `DecisionAgent` and `CommsAgent`
- `gemini` for live provider-backed `DecisionAgent` and `CommsAgent`

### 2. Start Redis

```bash
sudo systemctl start redis-server
redis-cli ping
```

Expected:

```text
PONG
```

### 3. Start the backend API

```bash
cd ~/Projects/P27/backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start the Celery worker

In a separate terminal:

```bash
cd ~/Projects/P27/backend
source .venv/bin/activate
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

### 5. Frontend setup

From repo root:

```bash
cd ~/Projects/P27
npm install
```

Start the web app:

```bash
cd ~/Projects/P27/frontend
npm run dev
```

Default frontend URL:

```text
http://localhost:3000
```

The frontend expects the backend API at:

```text
http://localhost:8000/api/v1
```

You can override that with `SPENDAGENT_API_BASE_URL` in `frontend/.env.local`.

## Validation commands

### Frontend

```bash
cd ~/Projects/P27
npm run build
```

### Backend

```bash
cd ~/Projects/P27/backend
source .venv/bin/activate
pytest
```

For targeted backend checks:

```bash
pytest tests/unit/test_provider_client.py
```

## How the system works

At a high level:

1. a user creates a renewal case
2. evidence is uploaded into the case
3. document and usage inputs are parsed into structured facts
4. the orchestration pipeline runs the analysis agents
5. a recommendation packet is produced with evidence and confidence
6. artifacts are generated for finance and vendor communication
7. the frontend presents the full audit trail to a human reviewer

This is the core distinction from a generic chat interface: the system is built around a case lifecycle and explicit operational artifacts, not prompt-by-prompt manual reasoning.

## Current limitations

- the system still depends on correct upstream evidence quality
- some routes currently rely on direct database access, not only Supabase REST
- outbound negotiation is drafted, not automatically sent
- the current UI is optimized for the renewal workflow, not yet for portfolio-level analytics
- local development still requires real infrastructure configuration for full end-to-end use

## Likely next improvements

- richer policy rules and approval thresholds
- better artifact quality for negotiation drafts
- more robust evidence conflict handling
- broader analytics views across vendors and upcoming renewals
- deeper Supabase-only integration where direct DB access is not required
- stronger automation around reviewer assignment and approval routing

## Project status

This repository is currently an MVP-oriented implementation of the SpendAgent workflow. It already supports a real case pipeline, a structured frontend workbench, and testable backend logic, but it is still in active product and engineering iteration.
