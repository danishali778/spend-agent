alter table public.agent_runs
  add column if not exists failure_category text;

alter table public.extracted_facts
  add column if not exists provenance_kind text not null default 'extracted',
  add column if not exists provenance_note text;

update public.extracted_facts
set provenance_kind = coalesce(provenance_kind, 'extracted')
where provenance_kind is null;
