from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any, Dict, Mapping, Optional, Protocol, Sequence, Tuple
from urllib import error as urllib_error
from urllib import request as urllib_request

from app.extractors.clause_locator import locate_clauses
from app.extractors.date_money_extractor import extract_iso_dates, extract_money_amounts
from app.parsers.email_parser import extract_email_fields
from app.parsers.pdf_parser import extract_pdf_text
from app.parsers.usage_csv import parse_csv_usage
from app.schemas.domain import FactProvenanceKind, ProjectedSavingsStatus


class ProviderClient(Protocol):
    def generate_json(self, agent_name: str, prompt_name: str, payload: Mapping[str, Any]) -> Dict[str, Any]: ...


class ProviderTransportError(RuntimeError):
    pass


class ProviderResponseError(ValueError):
    pass


def _decision_system_instruction() -> str:
    return (
        "You are SpendAgent's DecisionAgent. "
        "Return only valid JSON. "
        "Do not wrap JSON in markdown. "
        "Do not invent facts, savings, policy results, or evidence. "
        "You may choose only from: renew, downgrade, cancel, renegotiate, escalate."
    )


def _comms_system_instruction() -> str:
    return (
        "You are SpendAgent's CommsAgent. "
        "Return only valid JSON. "
        "Do not wrap JSON in markdown. "
        "Draft concise business artifacts using only supplied evidence."
    )


def _decision_required_shape() -> dict[str, Any]:
    return {
        "recommendedAction": "renew|downgrade|cancel|renegotiate|escalate",
        "confidenceScore": "float between 0 and 1",
        "rationale": "string",
        "evidence": [{"factKey": "string", "value": "string|number|boolean", "sourceDocumentId": "string"}],
        "projectedSavings": "number|null; must exactly match deterministic input",
        "projectedSavingsStatus": "calculated|not_available|needs_spend_data; must exactly match deterministic input",
        "blockers": ["string"],
        "nextStep": "string",
        "fallbackAction": "renew|downgrade|cancel|renegotiate|escalate|null",
    }


def _comms_required_shape() -> dict[str, Any]:
    return {
        "artifacts": [
            {
                "artifactType": "cfo_summary|approval_note|vendor_email",
                "title": "string",
                "content": "string",
                "decisionVersion": 1,
            }
        ]
    }


def _build_decision_prompt(prompt_name: str, payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            f"Prompt: {prompt_name}",
            "Task: choose the best recommended action using only the provided evidence and deterministic analysis.",
            "Style requirements:",
            "- rationale must be concise, direct, and limited to at most 2 sentences.",
            "- nextStep must be exactly 1 sentence and action-oriented.",
            "- blockers should be empty unless there is a real constraint from the supplied inputs.",
            "Hard rules:",
            "- Preserve projectedSavings exactly from financeAnalysis; do not recompute or modify it.",
            "- Preserve projectedSavingsStatus exactly from financeAnalysis.",
            "- Evidence must contain only the strongest 1 to 3 facts from documentAnalysis.",
            "- Every evidence item sourceDocumentId must come from documentAnalysis facts only.",
            "- Never use synthetic sourceDocumentId values such as financeAnalysis, policyEvaluation, case, or generated names.",
            "- You may reference finance metrics in rationale, but not as evidence items unless they already appear in documentAnalysis facts.",
            "- If the evidence is weak, you may choose escalate, but do not invent blockers.",
            "- Return JSON only.",
            "",
            "Required JSON shape:",
            json.dumps(_decision_required_shape(), indent=2),
            "",
            "Input state:",
            json.dumps(payload, indent=2, sort_keys=True),
        ]
    )


def _build_comms_prompt(prompt_name: str, payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            f"Prompt: {prompt_name}",
            "Task: draft the required three artifacts based only on the supplied case, decision, and extracted evidence.",
            "Artifact requirements:",
            "- cfo_summary: 2 to 3 sentences, executive tone, include recommended action and the core business reason.",
            "- approval_note: 1 to 2 sentences, crisp internal note, include confidence and immediate next step.",
            "- vendor_email: 3 to 5 sentences, professional external tone, ask to review renewal terms without overclaiming certainty.",
            "Hard rules:",
            "- Return exactly three artifacts: cfo_summary, approval_note, vendor_email.",
            "- Keep language concise, non-repetitive, and businesslike.",
            "- Do not repeat the same sentence structure across artifacts.",
            "- Do not add contract values, dates, or claims that are not present in the supplied payload.",
            "- Do not use bullet lists, markdown, or headings inside artifact content.",
            "- Return JSON only.",
            "",
            "Required JSON shape:",
            json.dumps(_comms_required_shape(), indent=2),
            "",
            "Input state:",
            json.dumps(payload, indent=2, sort_keys=True),
        ]
    )


def _decision_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "recommendedAction": {
                "type": "string",
                "enum": ["renew", "downgrade", "cancel", "renegotiate", "escalate"],
            },
            "confidenceScore": {"type": "number"},
            "rationale": {"type": "string"},
            "evidence": {
                "type": "array",
                "minItems": 0,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "factKey": {"type": "string"},
                        "value": {"type": ["string", "number", "boolean"]},
                        "sourceDocumentId": {"type": "string"},
                    },
                    "required": ["factKey", "value", "sourceDocumentId"],
                    "additionalProperties": False,
                },
            },
            "projectedSavings": {"type": ["number", "null"]},
            "projectedSavingsStatus": {
                "type": "string",
                "enum": ["calculated", "not_available", "needs_spend_data"],
            },
            "blockers": {"type": "array", "items": {"type": "string"}},
            "nextStep": {"type": "string"},
            "fallbackAction": {
                "type": ["string", "null"],
                "enum": ["renew", "downgrade", "cancel", "renegotiate", "escalate", None],
            },
        },
        "required": [
            "recommendedAction",
            "confidenceScore",
            "rationale",
            "evidence",
            "projectedSavings",
            "projectedSavingsStatus",
            "blockers",
            "nextStep",
            "fallbackAction",
        ],
        "additionalProperties": False,
    }


def _comms_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "artifacts": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "artifactType": {
                            "type": "string",
                            "enum": ["cfo_summary", "approval_note", "vendor_email"],
                        },
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "decisionVersion": {"type": "integer"},
                    },
                    "required": ["artifactType", "title", "content", "decisionVersion"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["artifacts"],
        "additionalProperties": False,
    }


class MockProviderClient:
    def __init__(self, overrides: Optional[Mapping[Tuple[str, str], Sequence[Mapping[str, Any]]]] = None) -> None:
        self.overrides = {key: [deepcopy(item) for item in value] for key, value in (overrides or {}).items()}

    def generate_json(self, agent_name: str, prompt_name: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        key = (agent_name, prompt_name)
        if key in self.overrides and self.overrides[key]:
            return deepcopy(self.overrides[key].pop(0))
        return self._default_response(agent_name, payload)

    def _default_response(self, agent_name: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        if agent_name == "DocumentAgent":
            return self._document_analysis(payload)
        if agent_name == "FinanceAgent":
            return self._finance_analysis(payload)
        if agent_name == "PolicyAgent":
            finance = payload.get("financeAnalysis") or {}
            usage = finance.get("usageSnapshot") or {}
            total_cost = usage.get("totalCost") or 0
            threshold_message = "The contract value requires CFO awareness but does not block the workflow." if total_cost and total_cost >= 25000 else "The action is within the default mock policy threshold."
            return {"checks": [{"thresholdName": "cfo_approval_over_25000", "result": "pass", "message": threshold_message}], "requiresEscalation": False}
        if agent_name == "DecisionAgent":
            return self._decision(payload)
        if agent_name == "CommsAgent":
            vendor_name = payload["case"].get("vendorName", "Vendor")
            decision = payload["decision"]
            evidence = decision.get("evidence", [])
            renewal_date = self._evidence_value(evidence, "renewal_date")
            notice_days = self._evidence_value(evidence, "termination_notice_days")
            purchased_seats = self._evidence_value(evidence, "seats_purchased")
            active_seats = self._evidence_value(evidence, "active_seats")
            savings = decision.get("projectedSavings")
            savings_phrase = f" with an estimated annual savings opportunity of ${savings:,.0f}" if isinstance(savings, (int, float)) else ""
            seat_phrase = self._seat_phrase(purchased_seats, active_seats)
            timing_phrase = self._timing_phrase(renewal_date, notice_days)
            return {
                "artifacts": [
                    {"artifactType": "cfo_summary", "title": f"Renewal Recommendation for {vendor_name}", "content": f"Recommend {decision['recommendedAction']} for {vendor_name}{savings_phrase}. {seat_phrase or 'The recommendation is based on the uploaded renewal evidence and usage signals.'}", "decisionVersion": 1},
                    {"artifactType": "approval_note", "title": f"Approval Note for {vendor_name}", "content": f"Decision confidence is {decision['confidenceScore']:.2f}. {decision['nextStep']}", "decisionVersion": 1},
                    {"artifactType": "vendor_email", "title": f"{vendor_name} Renewal Discussion", "content": self._vendor_email(vendor_name, decision, seat_phrase, timing_phrase, savings_phrase), "decisionVersion": 1},
                ]
            }
        raise ValueError(f"No mock response configured for {agent_name}")

    def _evidence_value(self, evidence: Sequence[Mapping[str, Any]], fact_key: str) -> Any:
        for item in evidence:
            if item.get("factKey") == fact_key:
                return item.get("value")
        return None

    def _seat_phrase(self, purchased_seats: Any, active_seats: Any) -> str:
        if purchased_seats is None or active_seats is None:
            return ""
        try:
            purchased = int(purchased_seats)
            active = int(active_seats)
        except (TypeError, ValueError):
            return ""
        if purchased <= 0:
            return ""
        utilization = round((active / purchased) * 100)
        return f"Usage evidence shows {active} active seats against {purchased} purchased seats, or about {utilization}% utilization."

    def _timing_phrase(self, renewal_date: Any, notice_days: Any) -> str:
        parts: list[str] = []
        if renewal_date:
            parts.append(f"the renewal date appears to be {renewal_date}")
        if notice_days:
            parts.append(f"the notice window is {notice_days} days")
        return " and ".join(parts)

    def _vendor_email(self, vendor_name: str, decision: Mapping[str, Any], seat_phrase: str, timing_phrase: str, savings_phrase: str) -> str:
        action = str(decision.get("recommendedAction", "review"))
        opening = f"Hi {vendor_name} team,"
        context_parts = []
        if seat_phrase:
            context_parts.append(seat_phrase)
        if timing_phrase:
            context_parts.append(f"We are reviewing this renewal because {timing_phrase}.")
        context = " ".join(context_parts) or "We are reviewing the upcoming renewal and want to align the subscription with current usage."
        savings_sentence = f"We would like to discuss options that better match current demand{savings_phrase}." if savings_phrase else "We would like to discuss options that better match current demand before we finalize the renewal."
        ask = "Could you share revised renewal options, including a right-sized seat count and any pricing flexibility available for this term?"
        close = "Thanks, and we would appreciate your response before the notice window closes."
        if action == "escalate":
            savings_sentence = "Before we proceed, we need to clarify the renewal terms and usage baseline."
        return "\n\n".join([opening, context, savings_sentence, ask, close])

    def _document_analysis(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        documents = payload.get("documents", [])
        case = payload.get("case", {})
        allow_mock_fallbacks = bool(payload.get("allowMockFallbacks"))
        facts: list[dict[str, Any]] = []
        ambiguities: list[str] = []
        missing_critical: list[str] = []
        missing_supporting: list[str] = []

        def add_fact(
            fact_key: str,
            value: Any,
            document_id: str,
            snippet: str,
            confidence: float,
            *,
            provenance_kind: FactProvenanceKind = FactProvenanceKind.EXTRACTED,
            provenance_note: str | None = None,
        ) -> None:
            facts.append(
                {
                    "factKey": fact_key,
                    "value": value,
                    "sourceDocumentId": document_id,
                    "sourceSnippet": snippet,
                    "confidenceScore": confidence,
                    "provenanceKind": provenance_kind.value,
                    "provenanceNote": provenance_note,
                }
            )

        for document in documents:
            document_type = document.get("type")
            raw_text = document.get("rawText") or ""
            document_id = str(document.get("id"))
            if document_type in {"contract_pdf", "invoice_pdf"}:
                extraction = extract_pdf_text(document_id, raw_text=raw_text)
                if extraction.status != "ok":
                    ambiguities.append(extraction.message or f"Unable to parse {document_type}")
                    continue
                clause_matches = locate_clauses(extraction.text, {"renewal": r"renew(?:s|al| automatically)?", "termination_notice": r"(notice|days prior to renewal|termination)", "seat_count": r"\b\d+\s+(?:Business\s+)?seats?\b"})
                dates = extract_iso_dates(extraction.text)
                if dates:
                    add_fact("renewal_date", dates[0], document_id, clause_matches[0].snippet if clause_matches else extraction.text[:160], 0.94)
                notice_match = re.search(r"(\d+)\s*days?\s+prior to renewal", extraction.text, flags=re.IGNORECASE)
                if notice_match:
                    add_fact("termination_notice_days", int(notice_match.group(1)), document_id, notice_match.group(0), 0.9)
                seats_match = re.search(r"(\d+)\s+(?:Business\s+)?seats?", extraction.text, flags=re.IGNORECASE)
                if seats_match:
                    add_fact("seats_purchased", int(seats_match.group(1)), document_id, seats_match.group(0), 0.91)
                amounts = extract_money_amounts(extraction.text)
                if amounts:
                    add_fact("annual_cost_usd", amounts[0].amount, document_id, amounts[0].raw, 0.97)
            elif document_type == "usage_csv":
                usage = parse_csv_usage(document_id, raw_text=raw_text)
                if usage.status != "ok":
                    ambiguities.append(usage.message or "Usage CSV could not be parsed")
                else:
                    add_fact("active_seats", usage.summary.active_users if usage.summary else 0, document_id, f"{usage.summary.active_users if usage.summary else 0} active users identified in usage export.", 0.99)
            elif document_type == "renewal_email":
                email = extract_email_fields(document_id, raw_text)
                if email.status != "ok":
                    ambiguities.append(email.message or "Renewal email could not be parsed")
                else:
                    body = email.body or raw_text
                    if email.detected_dates:
                        add_fact("renewal_date", email.detected_dates[0], document_id, body[:160], 0.72)
                    notice_match = re.search(r"(\d+)\s*days?\s+(?:before|prior to)\s+(?:the\s+)?renewal", body, flags=re.IGNORECASE)
                    if notice_match:
                        add_fact("termination_notice_days", int(notice_match.group(1)), document_id, notice_match.group(0), 0.83)
                    seats_match = re.search(r"(\d+)\s+(?:business\s+)?seats?", body, flags=re.IGNORECASE)
                    if seats_match:
                        add_fact("seats_purchased", int(seats_match.group(1)), document_id, seats_match.group(0), 0.8)
                    amounts = extract_money_amounts(body)
                    if amounts:
                        add_fact("annual_cost_usd", amounts[0].amount, document_id, amounts[0].raw, 0.86)
        if documents:
            fallback_document_id = str(documents[0].get("id"))
            contract_id = next((str(document.get("id")) for document in documents if document.get("type") == "contract_pdf"), fallback_document_id)
            usage_id = next((str(document.get("id")) for document in documents if document.get("type") == "usage_csv"), fallback_document_id)
            fact_keys = {fact["factKey"] for fact in facts}
            if allow_mock_fallbacks and case.get("renewalDate") and "renewal_date" not in fact_keys:
                add_fact("renewal_date", case["renewalDate"], contract_id, "Using case renewal date as mock fallback evidence.", 0.6, provenance_kind=FactProvenanceKind.INFERRED, provenance_note="mock_case_fallback")
            if allow_mock_fallbacks and "termination_notice_days" not in fact_keys:
                add_fact("termination_notice_days", 14, contract_id, "Fallback notice window for mock-mode execution.", 0.5, provenance_kind=FactProvenanceKind.INFERRED, provenance_note="mock_default_notice_window")
            if allow_mock_fallbacks and "seats_purchased" not in fact_keys:
                add_fact("seats_purchased", 250, contract_id, "Fallback purchased seat baseline for mock-mode execution.", 0.5, provenance_kind=FactProvenanceKind.INFERRED, provenance_note="mock_default_seat_baseline")
            if allow_mock_fallbacks and "active_seats" not in fact_keys:
                add_fact("active_seats", 46, usage_id, "Fallback active seat count for mock-mode execution.", 0.5, provenance_kind=FactProvenanceKind.INFERRED, provenance_note="mock_default_active_seats")
        keys = {fact["factKey"] for fact in facts}
        for critical in ("renewal_date", "termination_notice_days"):
            if critical not in keys:
                missing_critical.append(critical)
        for supporting in ("seats_purchased", "active_seats", "annual_cost_usd"):
            if supporting not in keys:
                missing_supporting.append(supporting)
        return {"facts": facts, "ambiguities": ambiguities, "missingCriticalFacts": missing_critical, "missingSupportingFacts": missing_supporting}

    def _finance_analysis(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        document_analysis = payload.get("documentAnalysis") or {}
        facts = {fact["factKey"]: fact["value"] for fact in document_analysis.get("facts", [])}
        seats_purchased = int(facts["seats_purchased"]) if "seats_purchased" in facts else None
        seats_active = int(facts["active_seats"]) if "active_seats" in facts else None
        total_cost = float(facts["annual_cost_usd"]) if "annual_cost_usd" in facts else None
        conflicts: list[str] = []
        utilization_percent = None
        if seats_purchased is None or seats_active is None:
            conflicts.append("Usage or seat baseline is incomplete.")
        elif seats_active > seats_purchased:
            conflicts.append("Active seats exceed purchased seats.")
        else:
            utilization_percent = round((seats_active / seats_purchased) * 100, 2) if seats_purchased else None
        projected_savings = None
        projected_savings_status = ProjectedSavingsStatus.NOT_AVAILABLE
        if seats_purchased and seats_active is not None and total_cost is not None and seats_purchased > 0:
            target_seats = max(seats_active * 2, 1)
            if target_seats < seats_purchased:
                projected_savings = round(total_cost * ((seats_purchased - target_seats) / seats_purchased), 2)
                projected_savings_status = ProjectedSavingsStatus.CALCULATED
        elif seats_purchased is not None and seats_active is not None and total_cost is None and not conflicts:
            projected_savings_status = ProjectedSavingsStatus.NEEDS_SPEND_DATA
        return {"usageSnapshot": {"seatsPurchased": seats_purchased, "seatsActive": seats_active, "utilizationPercent": utilization_percent, "totalCost": total_cost, "costPeriod": "annual" if total_cost is not None else None, "currency": "USD"}, "savingsScenarios": [{"action": "renegotiate", "projectedSavings": projected_savings, "projectedSavingsStatus": projected_savings_status.value, "summary": "Renegotiating to align seat count with usage creates savings potential."}] if projected_savings is not None else [], "projectedSavingsStatus": projected_savings_status.value, "conflicts": conflicts}

    def _decision(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        if payload.get("requiresEscalation"):
            reasons = payload.get("escalationReasons") or ["Critical evidence is missing."]
            return {"recommendedAction": "escalate", "confidenceScore": 0.34, "rationale": "Critical evidence is missing or conflicting, so a human review is required.", "evidence": [], "projectedSavings": None, "projectedSavingsStatus": ProjectedSavingsStatus.NOT_AVAILABLE.value, "blockers": reasons, "nextStep": "Review missing inputs and confirm renewal terms manually.", "fallbackAction": None}
        finance = payload.get("financeAnalysis") or {}
        usage = finance.get("usageSnapshot") or {}
        savings = finance.get("savingsScenarios") or []
        evidence = []
        sorted_facts = sorted(
            (payload.get("documentAnalysis") or {}).get("facts", []),
            key=lambda fact: (
                0 if fact.get("provenanceKind") == FactProvenanceKind.EXTRACTED.value else 1,
                -float(fact.get("confidenceScore") or 0),
            ),
        )
        for fact in sorted_facts[:3]:
            evidence.append(
                {
                    "factKey": fact.get("factKey", "unknown"),
                    "value": fact.get("value"),
                    "sourceDocumentId": fact.get("sourceDocumentId", "unknown"),
                    "sourceSnippet": fact.get("sourceSnippet", ""),
                    "confidenceScore": float(fact.get("confidenceScore") or 0),
                    "provenanceKind": fact.get("provenanceKind", FactProvenanceKind.EXTRACTED.value),
                }
            )
        utilization = usage.get("utilizationPercent")
        projected_savings = savings[0].get("projectedSavings") if savings else None
        projected_savings_status = finance.get("projectedSavingsStatus", ProjectedSavingsStatus.NOT_AVAILABLE.value)
        if savings and savings[0].get("projectedSavingsStatus"):
            projected_savings_status = savings[0]["projectedSavingsStatus"]
        if utilization is not None and utilization < 35:
            return {"recommendedAction": "renegotiate", "confidenceScore": 0.82, "rationale": "Low license utilization ahead of renewal supports a renegotiation recommendation.", "evidence": evidence, "projectedSavings": projected_savings, "projectedSavingsStatus": projected_savings_status or ProjectedSavingsStatus.NEEDS_SPEND_DATA.value, "blockers": [], "nextStep": "Review and send the negotiation draft before the notice window closes.", "fallbackAction": "downgrade"}
        return {"recommendedAction": "renew", "confidenceScore": 0.58, "rationale": "Available evidence does not support a stronger cost-reduction action.", "evidence": evidence, "projectedSavings": projected_savings, "projectedSavingsStatus": projected_savings_status, "blockers": [], "nextStep": "Review the available evidence and confirm whether more inputs are needed.", "fallbackAction": "escalate"}


class GroqProviderClient:
    endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        temperature: float = 0.1,
        deterministic_provider: ProviderClient | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("GROQ_API_KEY is required when SPENDAGENT_PROVIDER_MODE=groq.")
        if not model:
            raise ValueError("SPENDAGENT_GROQ_MODEL is required when SPENDAGENT_PROVIDER_MODE=groq.")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.deterministic_provider = deterministic_provider or MockProviderClient()

    def generate_json(self, agent_name: str, prompt_name: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        if agent_name not in {"DecisionAgent", "CommsAgent"}:
            return self.deterministic_provider.generate_json(agent_name, prompt_name, payload)

        body = {
            "model": self.model,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
            "messages": self._build_messages(agent_name, prompt_name, payload),
        }
        response = self._post_chat_completion(body)
        return self._extract_json_response(response, agent_name)

    def _build_messages(self, agent_name: str, prompt_name: str, payload: Mapping[str, Any]) -> list[dict[str, str]]:
        if agent_name == "DecisionAgent":
            return [
                {
                    "role": "system",
                    "content": _decision_system_instruction(),
                },
                {
                    "role": "user",
                    "content": _build_decision_prompt(prompt_name, payload),
                },
            ]
        if agent_name == "CommsAgent":
            return [
                {
                    "role": "system",
                    "content": _comms_system_instruction(),
                },
                {
                    "role": "user",
                    "content": _build_comms_prompt(prompt_name, payload),
                },
            ]
        raise ValueError(f"GroqProviderClient does not support agent {agent_name}")

    def _post_chat_completion(self, body: Mapping[str, Any]) -> Dict[str, Any]:
        encoded = json.dumps(body).encode("utf-8")
        request = urllib_request.Request(
            self.endpoint,
            data=encoded,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib_request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except urllib_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ProviderTransportError(f"Groq HTTP error {exc.code}: {detail or exc.reason}") from exc
        except urllib_error.URLError as exc:
            raise ProviderTransportError(f"Groq transport error: {exc.reason}") from exc
        except TimeoutError as exc:
            raise ProviderTransportError("Groq request timed out.") from exc

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ProviderResponseError("Groq returned non-JSON HTTP payload.") from exc
        if not isinstance(parsed, dict):
            raise ProviderResponseError("Groq returned an unexpected response envelope.")
        return parsed

    def _extract_json_response(self, response: Mapping[str, Any], agent_name: str) -> Dict[str, Any]:
        try:
            message = response["choices"][0]["message"]
            content = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError(f"Groq returned an invalid completion envelope for {agent_name}.") from exc

        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        if not isinstance(content, str) or not content.strip():
            raise ProviderResponseError(f"Groq returned empty content for {agent_name}.")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProviderResponseError(f"Groq returned invalid JSON content for {agent_name}.") from exc
        if not isinstance(parsed, dict):
            raise ProviderResponseError(f"Groq returned a non-object JSON payload for {agent_name}.")
        return parsed


class GeminiProviderClient:
    endpoint_template = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        temperature: float = 0.1,
        deterministic_provider: ProviderClient | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when SPENDAGENT_PROVIDER_MODE=gemini.")
        if not model:
            raise ValueError("SPENDAGENT_GEMINI_MODEL is required when SPENDAGENT_PROVIDER_MODE=gemini.")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.deterministic_provider = deterministic_provider or MockProviderClient()

    def generate_json(self, agent_name: str, prompt_name: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        if agent_name not in {"DecisionAgent", "CommsAgent"}:
            return self.deterministic_provider.generate_json(agent_name, prompt_name, payload)

        request_body = self._build_request(agent_name, prompt_name, payload)
        response = self._post_generate_content(request_body)
        return self._extract_json_response(response, agent_name)

    def _build_request(self, agent_name: str, prompt_name: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        if agent_name == "DecisionAgent":
            system_instruction = _decision_system_instruction()
            user_prompt = _build_decision_prompt(prompt_name, payload)
            schema = _decision_schema()
        elif agent_name == "CommsAgent":
            system_instruction = _comms_system_instruction()
            user_prompt = _build_comms_prompt(prompt_name, payload)
            schema = _comms_schema()
        else:
            raise ValueError(f"GeminiProviderClient does not support agent {agent_name}")

        return {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "responseMimeType": "application/json",
                "responseJsonSchema": schema,
            },
        }

    def _build_decision_prompt(self, prompt_name: str, payload: Mapping[str, Any]) -> str:
        return _build_decision_prompt(prompt_name, payload)

    def _build_comms_prompt(self, prompt_name: str, payload: Mapping[str, Any]) -> str:
        return _build_comms_prompt(prompt_name, payload)

    def _post_generate_content(self, body: Mapping[str, Any]) -> Dict[str, Any]:
        encoded = json.dumps(body).encode("utf-8")
        request = urllib_request.Request(
            self.endpoint_template.format(model=self.model),
            data=encoded,
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib_request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except urllib_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ProviderTransportError(f"Gemini HTTP error {exc.code}: {detail or exc.reason}") from exc
        except urllib_error.URLError as exc:
            raise ProviderTransportError(f"Gemini transport error: {exc.reason}") from exc
        except TimeoutError as exc:
            raise ProviderTransportError("Gemini request timed out.") from exc

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ProviderResponseError("Gemini returned non-JSON HTTP payload.") from exc
        if not isinstance(parsed, dict):
            raise ProviderResponseError("Gemini returned an unexpected response envelope.")
        return parsed

    def _extract_json_response(self, response: Mapping[str, Any], agent_name: str) -> Dict[str, Any]:
        try:
            content = response["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError(f"Gemini returned an invalid completion envelope for {agent_name}.") from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderResponseError(f"Gemini returned empty content for {agent_name}.")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProviderResponseError(f"Gemini returned invalid JSON content for {agent_name}.") from exc
        if not isinstance(parsed, dict):
            raise ProviderResponseError(f"Gemini returned a non-object JSON payload for {agent_name}.")
        return parsed


def create_provider_client(app_settings: Any) -> ProviderClient:
    mode = str(getattr(app_settings, "provider_mode", "mock")).lower()
    if mode == "mock":
        return MockProviderClient()
    if mode == "groq":
        return GroqProviderClient(
            api_key=str(getattr(app_settings, "groq_api_key", "")),
            model=str(getattr(app_settings, "groq_model", "")),
            timeout_seconds=float(getattr(app_settings, "groq_timeout_seconds", 30.0)),
            temperature=float(getattr(app_settings, "groq_temperature", 0.1)),
        )
    if mode == "gemini":
        return GeminiProviderClient(
            api_key=str(getattr(app_settings, "gemini_api_key", "")),
            model=str(getattr(app_settings, "gemini_model", "")),
            timeout_seconds=float(getattr(app_settings, "gemini_timeout_seconds", 30.0)),
            temperature=float(getattr(app_settings, "gemini_temperature", 0.1)),
        )
    raise ValueError(f"Unsupported provider mode: {mode}")
