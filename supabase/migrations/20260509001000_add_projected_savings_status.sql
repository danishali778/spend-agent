alter table public.cases
  add column if not exists projected_savings_status text;

update public.cases
set projected_savings_status = case
  when projected_savings is not null then 'calculated'
  else 'not_available'
end
where projected_savings_status is null;

alter table public.cases
  alter column projected_savings_status set default 'not_available';

alter table public.cases
  alter column projected_savings_status set not null;

alter table public.decisions
  add column if not exists projected_savings_status text;

update public.decisions
set projected_savings_status = case
  when projected_savings is not null then 'calculated'
  else 'not_available'
end
where projected_savings_status is null;

alter table public.decisions
  alter column projected_savings_status set default 'not_available';

alter table public.decisions
  alter column projected_savings_status set not null;
