# Autonomous Procurement Negotiation Agent

An autonomous multi-agent procurement analyst that reads contracts, spend, usage, and renewal signals to recommend the best vendor action and draft the next move.

## Problem

Finance teams lose money on software renewals because the signals that matter are fragmented across contracts, invoices, usage exports, and email reminders. By the time someone notices underused licenses or an unfavorable auto-renewal clause, the negotiation window is gone.

## Target Buyer

Primary buyer: CFO or finance leader.

Secondary users:
- procurement manager
- IT operations
- finance analyst

## Why Autonomy Matters

This system is not a copilot waiting for prompts. It ingests documents, extracts structured evidence, runs financial and policy analysis, chooses a recommended action, and drafts the next artifacts needed to execute that action. Human review remains required for outbound steps, but the decision workflow is autonomous.

## System Summary

The product is a monorepo MVP built with a `Next.js` frontend in `frontend/`, a Python `FastAPI + Celery` backend in `backend/`, and `Supabase Postgres`. Users create a procurement case, upload a contract PDF, invoice PDF, usage CSV, and renewal email, then trigger analysis. A multi-agent system parses the inputs, computes utilization and savings opportunities, evaluates renewal constraints, recommends one of `renew`, `downgrade`, `cancel`, `renegotiate`, or `escalate`, and generates a CFO memo plus vendor-facing negotiation draft.

## Local Development

- Frontend lives in `frontend/`.
- Backend lives in `backend/`.
- Run backend commands from `backend/.venv`.

## Repo Map

- Architecture: [docs/architecture/architecture.md](/e:/Projects/P27/docs/architecture/architecture.md)
- Folder structure: [docs/architecture/folder-structure.md](/e:/Projects/P27/docs/architecture/folder-structure.md)
- Data model: [docs/architecture/data-model.md](/e:/Projects/P27/docs/architecture/data-model.md)
- API contracts: [docs/api/api-spec.md](/e:/Projects/P27/docs/api/api-spec.md)
- Agent design: [docs/agents/agents.md](/e:/Projects/P27/docs/agents/agents.md)
- Prompt contracts: [docs/agents/prompts.md](/e:/Projects/P27/docs/agents/prompts.md)
- Tool contracts: [docs/agents/tool-contracts.md](/e:/Projects/P27/docs/agents/tool-contracts.md)
- Product requirements: [docs/product/prd.md](/e:/Projects/P27/docs/product/prd.md)
- UI screens: [docs/ui/screens.md](/e:/Projects/P27/docs/ui/screens.md)
- Demo case: [docs/demo/sample-case.md](/e:/Projects/P27/docs/demo/sample-case.md)
- Demo script: [docs/demo/demo-script.md](/e:/Projects/P27/docs/demo/demo-script.md)
- 24-hour build plan: [docs/plan/hackathon-mvp-24h.md](/e:/Projects/P27/docs/plan/hackathon-mvp-24h.md)

## 3-Minute Demo

1. Create a case for a SaaS vendor renewal.
2. Upload the contract, invoice, usage export, and renewal email.
3. Start analysis and show the agent activity timeline.
4. Open the extracted evidence and point out the renewal deadline, license count, and low utilization.
5. Reveal the decision packet with projected savings and recommended action.
6. Open the generated CFO summary and vendor negotiation email draft.

## What Makes This Different From a Copilot

- It plans and executes a multi-step workflow without the user driving each step.
- It combines structured business rules with LLM reasoning instead of just summarizing text.
- It shows agent collaboration and evidence provenance.
- It produces actionable outputs for enterprise users, not generic chat responses.
