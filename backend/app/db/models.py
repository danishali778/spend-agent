from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CaseRow(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    vendor_name: Mapped[str] = mapped_column(Text)
    owner_user_id: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    renewal_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    urgency_level: Mapped[str | None] = mapped_column(String, nullable=True)
    projected_savings: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    projected_savings_status: Mapped[str] = mapped_column(String, default="not_available")
    recommended_action: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    type: Mapped[str] = mapped_column(String)
    source_name: Mapped[str] = mapped_column(Text)
    storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_status: Mapped[str] = mapped_column(String)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentRunRow(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    status: Mapped[str] = mapped_column(String)
    triggered_by_user_id: Mapped[str] = mapped_column(String)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_category: Mapped[str | None] = mapped_column(String, nullable=True)
    prompt_bundle_version: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentStepRow(Base):
    __tablename__ = "agent_steps"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"))
    agent_name: Mapped[str] = mapped_column(String)
    step_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class ExtractedFactRow(Base):
    __tablename__ = "extracted_facts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    fact_key: Mapped[str] = mapped_column(String)
    fact_value_json: Mapped[Any] = mapped_column(JSON)
    source_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric)
    provenance_kind: Mapped[str] = mapped_column(String, default="extracted")
    provenance_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_by_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UsageSnapshotRow(Base):
    __tablename__ = "usage_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    seats_purchased: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seats_active: Mapped[int | None] = mapped_column(Integer, nullable=True)
    utilization_percent: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    cost_period: Mapped[str | None] = mapped_column(String, nullable=True)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    currency: Mapped[str | None] = mapped_column(String, nullable=True)
    snapshot_source: Mapped[str] = mapped_column(String)
    created_by_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PolicyCheckRow(Base):
    __tablename__ = "policy_checks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"))
    proposed_action: Mapped[str] = mapped_column(String)
    threshold_name: Mapped[str] = mapped_column(String)
    result: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DecisionRow(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"))
    decision_version: Mapped[int] = mapped_column(Integer)
    recommended_action: Mapped[str] = mapped_column(String)
    fallback_action: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric)
    rationale: Mapped[str] = mapped_column(Text)
    projected_savings: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    projected_savings_status: Mapped[str] = mapped_column(String, default="not_available")
    blockers_json: Mapped[Any] = mapped_column(JSON)
    next_step: Mapped[str] = mapped_column(Text)
    evidence_json: Mapped[Any] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GeneratedArtifactRow(Base):
    __tablename__ = "generated_artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    decision_id: Mapped[str] = mapped_column(ForeignKey("decisions.id"))
    artifact_type: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
