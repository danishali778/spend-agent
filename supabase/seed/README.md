# SpendAgent Seed Fixtures

This directory contains canonical demo seed data for the `SpendAgent` MVP.

## Files

- `fixtures/acme-pm-suite.json`: the authoritative golden-path seed fixture for the demo case

## Conventions

- Public API-facing models use camelCase.
- Database-shaped records use snake_case and map directly to the tables documented in `docs/architecture/data-model.md`.
- All timestamps are fixed to deterministic ISO 8601 values to make tests and screenshots reproducible.
- `promptBundleVersion` must stay aligned with `packages/prompt-contracts/src/schemas.json`.
