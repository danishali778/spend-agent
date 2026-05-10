insert into public.cases (
  id, vendor_name, owner_user_id, status, renewal_date, urgency_level, projected_savings, recommended_action
)
values (
  '11111111-1111-1111-1111-111111111111',
  'Acme PM Suite',
  '00000000-0000-0000-0000-000000000001',
  'decision_ready',
  '2026-06-18T00:00:00Z',
  'high',
  18240.00,
  'renegotiate'
)
on conflict (id) do nothing;

insert into public.documents (id, case_id, type, source_name, raw_text, parse_status)
values
  (
    '22222222-2222-2222-2222-222222222221',
    '11111111-1111-1111-1111-111111111111',
    'contract_pdf',
    'acme-master-agreement.pdf',
    'This Agreement renews automatically on June 18, 2026 for an additional twelve-month term unless either party provides written notice at least fourteen (14) days prior to renewal.',
    'parsed'
  ),
  (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'invoice_pdf',
    'acme-invoice-2026.pdf',
    'Annual subscription charge: USD 48,000 for 250 Business seats.',
    'parsed'
  ),
  (
    '22222222-2222-2222-2222-222222222223',
    '11111111-1111-1111-1111-111111111111',
    'usage_csv',
    'acme-usage.csv',
    'active_users=46,total_users=250',
    'parsed'
  ),
  (
    '22222222-2222-2222-2222-222222222224',
    '11111111-1111-1111-1111-111111111111',
    'renewal_email',
    'renewal-reminder',
    'Your annual renewal is scheduled for June 18. Please contact your account representative if you wish to discuss your upcoming term.',
    'parsed'
  )
on conflict (id) do nothing;

insert into public.agent_runs (
  id, case_id, status, triggered_by_user_id, started_at, completed_at, prompt_bundle_version
)
values (
  '33333333-3333-3333-3333-333333333333',
  '11111111-1111-1111-1111-111111111111',
  'completed',
  '00000000-0000-0000-0000-000000000001',
  '2026-05-08T12:00:00Z',
  '2026-05-08T12:00:12Z',
  'v1.0.0'
)
on conflict (id) do nothing;

insert into public.extracted_facts (
  id, case_id, document_id, fact_key, fact_value_json, source_snippet, confidence_score, extracted_by_run_id
)
values
  (
    '44444444-4444-4444-4444-444444444441',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222221',
    'renewal_date',
    '\"2026-06-18\"'::jsonb,
    'This Agreement renews automatically on June 18, 2026',
    0.93,
    '33333333-3333-3333-3333-333333333333'
  ),
  (
    '44444444-4444-4444-4444-444444444442',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222221',
    'termination_notice_days',
    '14'::jsonb,
    'written notice at least fourteen (14) days prior to renewal',
    0.89,
    '33333333-3333-3333-3333-333333333333'
  ),
  (
    '44444444-4444-4444-4444-444444444443',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    'annual_cost_usd',
    '48000'::jsonb,
    'Annual subscription charge: USD 48,000',
    0.97,
    '33333333-3333-3333-3333-333333333333'
  ),
  (
    '44444444-4444-4444-4444-444444444444',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222223',
    'seats_active',
    '46'::jsonb,
    'active_users=46',
    1.0,
    '33333333-3333-3333-3333-333333333333'
  )
on conflict (id) do nothing;

insert into public.usage_snapshots (
  id, case_id, seats_purchased, seats_active, utilization_percent, cost_period, total_cost, currency, snapshot_source, created_by_run_id
)
values (
  '55555555-5555-5555-5555-555555555555',
  '11111111-1111-1111-1111-111111111111',
  250,
  46,
  18.40,
  'annual',
  48000.00,
  'USD',
  'merged',
  '33333333-3333-3333-3333-333333333333'
)
on conflict (id) do nothing;

insert into public.policy_checks (
  id, case_id, run_id, proposed_action, threshold_name, result, message
)
values (
  '66666666-6666-6666-6666-666666666666',
  '11111111-1111-1111-1111-111111111111',
  '33333333-3333-3333-3333-333333333333',
  'renegotiate',
  'cfo_approval_over_25000',
  'pass',
  'CFO review required but no additional legal review is needed for the negotiation draft.'
)
on conflict (id) do nothing;

insert into public.decisions (
  id, case_id, run_id, decision_version, recommended_action, fallback_action, confidence_score, rationale, projected_savings, blockers_json, next_step, evidence_json
)
values (
  '77777777-7777-7777-7777-777777777777',
  '11111111-1111-1111-1111-111111111111',
  '33333333-3333-3333-3333-333333333333',
  1,
  'renegotiate',
  'downgrade',
  0.82,
  'Vendor is materially underutilized ahead of a near-term renewal.',
  18240.00,
  '[]'::jsonb,
  'Review and send the negotiation draft before the notice window closes.',
  '[{\"factKey\":\"seats_active\",\"value\":46,\"sourceDocumentId\":\"22222222-2222-2222-2222-222222222223\"}]'::jsonb
)
on conflict (case_id, decision_version) do nothing;

insert into public.generated_artifacts (
  id, case_id, decision_id, artifact_type, title, content
)
values
  (
    '88888888-8888-8888-8888-888888888881',
    '11111111-1111-1111-1111-111111111111',
    '77777777-7777-7777-7777-777777777777',
    'cfo_summary',
    'Renewal Recommendation for Acme PM Suite',
    'Acme PM Suite is renewing in 41 days with only 18.4% observed license utilization. We recommend opening a renegotiation before the notice window closes.'
  ),
  (
    '88888888-8888-8888-8888-888888888882',
    '11111111-1111-1111-1111-111111111111',
    '77777777-7777-7777-7777-777777777777',
    'approval_note',
    'Approval Note for Acme PM Suite',
    'Finance review indicates a meaningful savings opportunity if the vendor agrees to reduce the committed seat baseline.'
  ),
  (
    '88888888-8888-8888-8888-888888888883',
    '11111111-1111-1111-1111-111111111111',
    '77777777-7777-7777-7777-777777777777',
    'vendor_email',
    'Seat Reduction and Renewal Discussion',
    'We are reviewing current utilization ahead of renewal and would like to discuss a revised seat commitment aligned with present usage.'
  )
on conflict (decision_id, artifact_type) do nothing;

insert into public.agent_steps (
  id, run_id, agent_name, step_name, status, summary, started_at, completed_at, retry_count
)
values
  (
    '99999999-9999-9999-9999-999999999991',
    '33333333-3333-3333-3333-333333333333',
    'DocumentAgent',
    'extract-contract-facts',
    'completed',
    'Identified renewal date, notice period, and cost clauses.',
    '2026-05-08T12:00:00Z',
    '2026-05-08T12:00:04Z',
    0
  ),
  (
    '99999999-9999-9999-9999-999999999992',
    '33333333-3333-3333-3333-333333333333',
    'FinanceAgent',
    'compute-utilization',
    'completed',
    'Calculated 18.4% license utilization and generated savings scenarios.',
    '2026-05-08T12:00:04Z',
    '2026-05-08T12:00:07Z',
    0
  ),
  (
    '99999999-9999-9999-9999-999999999993',
    '33333333-3333-3333-3333-333333333333',
    'DecisionAgent',
    'choose-action',
    'completed',
    'Selected renegotiate with downgrade as fallback.',
    '2026-05-08T12:00:07Z',
    '2026-05-08T12:00:09Z',
    0
  ),
  (
    '99999999-9999-9999-9999-999999999994',
    '33333333-3333-3333-3333-333333333333',
    'CommsAgent',
    'generate-artifacts',
    'completed',
    'Drafted CFO summary, approval note, and vendor email.',
    '2026-05-08T12:00:09Z',
    '2026-05-08T12:00:12Z',
    0
  )
on conflict (id) do nothing;

