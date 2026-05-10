from __future__ import annotations

from app.services.provider_client import MockProviderClient


def test_mock_provider_document_analysis_produces_fallback_facts() -> None:
    client = MockProviderClient()
    payload = {
        "case": {"vendorName": "Alpha CRM", "renewalDate": "2026-07-01T00:00:00+00:00"},
        "allowMockFallbacks": True,
        "documents": [
            {
                "id": "doc-email",
                "type": "renewal_email",
                "rawText": "Subject: Renewal reminder\n\nRenews on 2026-07-01.",
            }
        ],
    }

    response = client.generate_json("DocumentAgent", "run", payload)
    fact_keys = {item["factKey"] for item in response["facts"]}
    fact_document_ids = {item["sourceDocumentId"] for item in response["facts"]}

    assert "renewal_date" in fact_keys
    assert "termination_notice_days" in fact_keys
    assert "seats_purchased" in fact_keys
    assert "active_seats" in fact_keys
    assert fact_document_ids == {"doc-email"}
    fact_map = {item["factKey"]: item for item in response["facts"]}
    assert fact_map["termination_notice_days"]["provenanceKind"] == "inferred"
    assert fact_map["active_seats"]["provenanceKind"] == "inferred"


def test_mock_provider_document_analysis_extracts_email_spend_inputs() -> None:
    client = MockProviderClient()
    payload = {
        "case": {"vendorName": "Fresh Flow Test B", "renewalDate": "2026-10-15T00:00:00+00:00"},
        "documents": [
            {
                "id": "doc-email",
                "type": "renewal_email",
                "rawText": (
                    "Subject: Renewal Reminder\n\n"
                    "Renews on 2026-10-15.\n"
                    "Any cancellation or downgrade must be submitted at least 21 days before the renewal date.\n"
                    "Current plan includes 150 business seats.\n"
                    "Annual contract value: $36,000.\n"
                ),
            }
        ],
    }

    response = client.generate_json("DocumentAgent", "run", payload)
    facts = {item["factKey"]: item["value"] for item in response["facts"]}

    assert facts["renewal_date"] == "2026-10-15"
    assert facts["termination_notice_days"] == 21
    assert facts["seats_purchased"] == 150
    assert facts["annual_cost_usd"] == 36000.0


def test_mock_provider_document_analysis_disables_demo_fallbacks_when_requested() -> None:
    client = MockProviderClient()
    payload = {
        "case": {"vendorName": "Missing Spend Vendor", "renewalDate": "2026-12-01T00:00:00+00:00"},
        "allowMockFallbacks": False,
        "documents": [
            {
                "id": "doc-email",
                "type": "renewal_email",
                "rawText": (
                    "Subject: Renewal Reminder\n\n"
                    "This is a reminder that your subscription renews on 2026-12-01.\n"
                    "Current plan details:\n"
                    "- 120 business seats\n"
                ),
            }
        ],
    }

    response = client.generate_json("DocumentAgent", "run", payload)
    fact_keys = {item["factKey"] for item in response["facts"]}

    assert "renewal_date" in fact_keys
    assert "seats_purchased" in fact_keys
    assert "termination_notice_days" not in fact_keys
    assert "active_seats" not in fact_keys


def test_mock_provider_finance_analysis_marks_missing_spend_data() -> None:
    client = MockProviderClient()
    response = client.generate_json(
        "FinanceAgent",
        "run",
        {
            "documentAnalysis": {
                "facts": [
                    {"factKey": "seats_purchased", "value": 150},
                    {"factKey": "active_seats", "value": 28},
                ]
            }
        },
    )

    assert response["projectedSavingsStatus"] == "needs_spend_data"
    assert response["savingsScenarios"] == []


def test_mock_provider_finance_analysis_reports_conflict_when_active_exceeds_purchased() -> None:
    client = MockProviderClient()
    response = client.generate_json(
        "FinanceAgent",
        "run",
        {
            "documentAnalysis": {
                "facts": [
                    {"factKey": "seats_purchased", "value": 50},
                    {"factKey": "active_seats", "value": 80},
                    {"factKey": "annual_cost_usd", "value": 12000},
                ]
            }
        },
    )

    assert response["conflicts"] == ["Active seats exceed purchased seats."]
    assert response["projectedSavingsStatus"] == "not_available"
