create extension if not exists "pgcrypto";

do $$
begin
  if not exists (select 1 from pg_type where typname = 'case_status') then
    create type case_status as enum ('draft', 'ingested', 'analyzing', 'decision_ready', 'needs_review', 'archived');
  end if;
  if not exists (select 1 from pg_type where typname = 'document_type') then
    create type document_type as enum ('contract_pdf', 'invoice_pdf', 'usage_csv', 'renewal_email');
  end if;
  if not exists (select 1 from pg_type where typname = 'recommended_action') then
    create type recommended_action as enum ('renew', 'downgrade', 'cancel', 'renegotiate', 'escalate');
  end if;
  if not exists (select 1 from pg_type where typname = 'run_status') then
    create type run_status as enum ('queued', 'running', 'completed', 'failed', 'cancelled');
  end if;
  if not exists (select 1 from pg_type where typname = 'step_status') then
    create type step_status as enum ('pending', 'running', 'completed', 'failed', 'skipped');
  end if;
end $$;

create table if not exists public.cases (
  id uuid primary key default gen_random_uuid(),
  vendor_name text not null,
  owner_user_id uuid not null,
  status case_status not null default 'draft',
  renewal_date timestamptz,
  urgency_level text,
  projected_savings numeric(12,2),
  recommended_action recommended_action,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references public.cases(id) on delete cascade,
  type document_type not null,
  source_name text not null,
  storage_path text,
  raw_text text,
  mime_type text,
  parse_status text not null default 'pending',
  uploaded_at timestamptz not null default now()
);

create table if not exists public.agent_runs (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references public.cases(id) on delete cascade,
  status run_status not null default 'queued',
  triggered_by_user_id uuid not null,
  started_at timestamptz,
  completed_at timestamptz,
  failure_reason text,
  prompt_bundle_version text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.extracted_facts (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references public.cases(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  fact_key text not null,
  fact_value_json jsonb not null,
  source_snippet text,
  source_page integer,
  confidence_score numeric(4,3) not null check (confidence_score >= 0 and confidence_score <= 1),
  extracted_by_run_id uuid not null references public.agent_runs(id) on delete cascade,
  created_at timestamptz not null default now()
);

create table if not exists public.usage_snapshots (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references public.cases(id) on delete cascade,
  seats_purchased integer,
  seats_active integer,
  utilization_percent numeric(5,2),
  cost_period text,
  total_cost numeric(12,2),
  currency text not null,
  snapshot_source text not null,
  created_by_run_id uuid not null references public.agent_runs(id) on delete cascade,
  created_at timestamptz not null default now()
);

create table if not exists public.policy_checks (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references public.cases(id) on delete cascade,
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  proposed_action recommended_action not null,
  threshold_name text not null,
  result text not null,
  message text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.decisions (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references public.cases(id) on delete cascade,
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  decision_version integer not null,
  recommended_action recommended_action not null,
  fallback_action recommended_action,
  confidence_score numeric(4,3) not null check (confidence_score >= 0 and confidence_score <= 1),
  rationale text not null,
  projected_savings numeric(12,2),
  blockers_json jsonb not null default '[]'::jsonb,
  next_step text not null,
  evidence_json jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  unique (case_id, decision_version)
);

create table if not exists public.generated_artifacts (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references public.cases(id) on delete cascade,
  decision_id uuid not null references public.decisions(id) on delete cascade,
  artifact_type text not null,
  title text not null,
  content text not null,
  created_at timestamptz not null default now(),
  unique (decision_id, artifact_type)
);

create table if not exists public.agent_steps (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  agent_name text not null,
  step_name text not null,
  status step_status not null,
  summary text,
  started_at timestamptz,
  completed_at timestamptz,
  retry_count integer not null default 0,
  error_json jsonb
);

create index if not exists idx_cases_status on public.cases(status);
create index if not exists idx_cases_renewal_date on public.cases(renewal_date);
create index if not exists idx_cases_owner_status on public.cases(owner_user_id, status);
create index if not exists idx_documents_case_id on public.documents(case_id);
create index if not exists idx_documents_case_type on public.documents(case_id, type);
create index if not exists idx_runs_case_id on public.agent_runs(case_id);
create index if not exists idx_runs_status on public.agent_runs(status);
create index if not exists idx_facts_case_id on public.extracted_facts(case_id);
create index if not exists idx_facts_case_key on public.extracted_facts(case_id, fact_key);
create index if not exists idx_facts_document_id on public.extracted_facts(document_id);
create index if not exists idx_usage_case_id on public.usage_snapshots(case_id);
create index if not exists idx_policy_case_id on public.policy_checks(case_id);
create index if not exists idx_policy_run_id on public.policy_checks(run_id);
create index if not exists idx_decisions_case_id on public.decisions(case_id);
create index if not exists idx_decisions_case_version on public.decisions(case_id, decision_version desc);
create index if not exists idx_decisions_run_id on public.decisions(run_id);
create index if not exists idx_artifacts_case_id on public.generated_artifacts(case_id);
create index if not exists idx_steps_run_id on public.agent_steps(run_id);
create index if not exists idx_steps_run_started on public.agent_steps(run_id, started_at);

