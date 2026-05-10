insert into storage.buckets (id, name, public)
values
  ('contracts', 'contracts', false),
  ('invoices', 'invoices', false),
  ('usage-exports', 'usage-exports', false),
  ('renewal-emails', 'renewal-emails', false)
on conflict (id) do nothing;

