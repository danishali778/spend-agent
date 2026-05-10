from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RunStage(str, Enum):
    INPUT_PREP = "input_prep"
    DOCUMENT_ANALYSIS = "document_analysis"
    FINANCE_ANALYSIS = "finance_analysis"
    POLICY_CHECK = "policy_check"
    DECISION = "decision"
    ARTIFACT_GENERATION = "artifact_generation"
    PERSISTENCE = "persistence"


TERMINAL_STAGE_ORDER = [RunStage.INPUT_PREP, RunStage.DOCUMENT_ANALYSIS, RunStage.FINANCE_ANALYSIS, RunStage.POLICY_CHECK, RunStage.DECISION, RunStage.ARTIFACT_GENERATION, RunStage.PERSISTENCE]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class StageSnapshot:
    stage: RunStage
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0
    summary: str | None = None
    error: dict | None = None


@dataclass
class RunStateMachine:
    stage_order: list[RunStage] = field(default_factory=lambda: TERMINAL_STAGE_ORDER.copy())
    stages: dict[RunStage, StageSnapshot] = field(init=False)
    current_stage: RunStage | None = None

    def __post_init__(self) -> None:
        self.stages = {stage: StageSnapshot(stage=stage) for stage in self.stage_order}

    def start_stage(self, stage: RunStage) -> StageSnapshot:
        snapshot = self.stages[stage]
        snapshot.status = StageStatus.RUNNING
        snapshot.started_at = utc_now()
        snapshot.error = None
        self.current_stage = stage
        return snapshot

    def complete_stage(self, stage: RunStage, summary: str | None = None) -> StageSnapshot:
        snapshot = self.stages[stage]
        snapshot.status = StageStatus.COMPLETED
        snapshot.completed_at = utc_now()
        snapshot.summary = summary
        self.current_stage = None
        return snapshot

    def fail_stage(self, stage: RunStage, error: dict, retrying: bool) -> StageSnapshot:
        snapshot = self.stages[stage]
        snapshot.error = error
        snapshot.completed_at = utc_now()
        snapshot.retry_count += 1
        snapshot.status = StageStatus.PENDING if retrying else StageStatus.FAILED
        self.current_stage = None
        return snapshot
