"""Shared persistence spine used by new cross-module workflows."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class ConsentRecord(UUIDPrimaryKey, Base):
    """Append-only consent decision; the latest event determines current state."""

    __tablename__ = "consent_records"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('personalized_advice', 'offline_storage', "
            "'speech_audio_transcription', 'disease_problem_sync', 'research')",
            name="ck_consent_records_purpose",
        ),
        CheckConstraint(
            "decision IN ('granted', 'denied', 'withdrawn')",
            name="ck_consent_records_decision",
        ),
        CheckConstraint(
            "channel IN ('explicit_tap', 'voice_confirmed', 'settings', 'system_import')",
            name="ck_consent_records_channel",
        ),
        CheckConstraint("version > 0", name="ck_consent_records_version_positive"),
        UniqueConstraint("farmer_id", "idempotency_key", name="uq_consent_records_request"),
        UniqueConstraint(
            "farmer_id", "purpose", "version", name="uq_consent_records_purpose_version"
        ),
        Index("ix_consent_records_farmer_purpose_version", "farmer_id", "purpose", "version"),
    )

    farmer_id: Mapped[UUID] = mapped_column(
        ForeignKey("farmers.id", ondelete="RESTRICT"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(String(48), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(80), nullable=False)
    channel: Mapped[str] = mapped_column(String(24), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EvidenceArtifact(UUIDPrimaryKey, TimestampMixin, Base):
    """Immutable registry entry for a versioned source/cache artifact."""

    __tablename__ = "evidence_artifacts"
    __table_args__ = (
        CheckConstraint(
            "quality_status IN ('verified', 'provisional', 'synthetic', 'stale', 'unavailable')",
            name="ck_evidence_artifacts_quality",
        ),
        CheckConstraint(
            "coverage_end IS NULL OR coverage_start IS NULL OR coverage_end >= coverage_start",
            name="ck_evidence_artifacts_coverage",
        ),
        CheckConstraint("size_bytes IS NULL OR size_bytes > 0", name="ck_evidence_artifacts_size"),
        CheckConstraint(
            "spatial_resolution_m IS NULL OR spatial_resolution_m > 0",
            name="ck_evidence_artifacts_resolution",
        ),
        UniqueConstraint(
            "source_name", "dataset_id", "dataset_version", "checksum_sha256",
            name="uq_evidence_artifact_release_checksum",
        ),
        Index("ix_evidence_artifacts_dataset_version", "dataset_id", "dataset_version"),
    )

    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(160), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(120), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    relative_path: Mapped[str | None] = mapped_column(String(500))
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    units: Mapped[str | None] = mapped_column(String(60))
    license: Mapped[str] = mapped_column(String(240), nullable=False)
    coverage_start: Mapped[date | None] = mapped_column(Date)
    coverage_end: Mapped[date | None] = mapped_column(Date)
    spatial_resolution_m: Mapped[float | None] = mapped_column()
    quality_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="verified", server_default=text("'verified'")
    )
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AnalysisRecord(UUIDPrimaryKey, TimestampMixin, Base):
    """Versioned, reproducible analytical input/output envelope."""

    __tablename__ = "analysis_records"
    __table_args__ = (
        CheckConstraint(
            "record_type IN ('district_climate_bundle', 'planting_window_advisory', "
            "'rotation_comparison', 'adaptive_recommendation', 'evidence_summary')",
            name="ck_analysis_records_type",
        ),
        CheckConstraint(
            "status IN ('available', 'insufficient_data', 'provisional', 'unavailable')",
            name="ck_analysis_records_status",
        ),
        CheckConstraint(
            "(farmer_id IS NULL AND farmland_id IS NULL) OR "
            "(farmer_id IS NOT NULL AND farmland_id IS NOT NULL)",
            name="ck_analysis_records_owner_pair",
        ),
        ForeignKeyConstraint(
            ["farmland_id", "farmer_id"],
            ["farmlands.id", "farmlands.farmer_id"],
            name="fk_analysis_records_farmland_owner",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("record_type", "request_fingerprint", name="uq_analysis_request_fingerprint"),
        Index("ix_analysis_records_farm_created", "farmland_id", "created_at"),
        Index("ix_analysis_records_type_created", "record_type", "created_at"),
    )

    farmer_id: Mapped[UUID | None] = mapped_column(ForeignKey("farmers.id", ondelete="RESTRICT"))
    farmland_id: Mapped[UUID | None] = mapped_column()
    record_type: Mapped[str] = mapped_column(String(40), nullable=False)
    contract_version: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    output_document: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AnalysisRecordSource(Base):
    """Normalized link from an analytical result to exact source releases."""

    __tablename__ = "analysis_record_sources"
    __table_args__ = (
        CheckConstraint(
            "relation_kind IN ('input', 'validation', 'comparison')",
            name="ck_analysis_record_sources_relation",
        ),
        Index("ix_analysis_record_sources_artifact", "artifact_id"),
    )

    analysis_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_records.id", ondelete="CASCADE"), primary_key=True
    )
    artifact_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_artifacts.id", ondelete="RESTRICT"), primary_key=True
    )
    relation_kind: Mapped[str] = mapped_column(String(16), nullable=False, default="input")


class AdaptivePolicyVersion(UUIDPrimaryKey, Base):
    """Reviewed, versioned policy rules; never a live mutable singleton."""

    __tablename__ = "adaptive_policy_versions"
    __table_args__ = (
        CheckConstraint(
            "scope IN ('global', 'division', 'district', 'crop')",
            name="ck_adaptive_policy_scope",
        ),
        CheckConstraint(
            "review_status IN ('draft', 'in_review', 'approved', 'rejected', 'retired')",
            name="ck_adaptive_policy_review_status",
        ),
        CheckConstraint("version > 0", name="ck_adaptive_policy_version_positive"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_adaptive_policy_effective_dates",
        ),
        UniqueConstraint("policy_key", "version", name="uq_adaptive_policy_key_version"),
        Index("ix_adaptive_policy_scope_review", "scope", "review_status", "effective_from"),
    )

    policy_key: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)
    region_code: Mapped[str | None] = mapped_column(String(32))
    crop_code: Mapped[str | None] = mapped_column(String(80))
    policy_document: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    source_references: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    review_status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("farmers.id", ondelete="RESTRICT"))
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("farmers.id", ondelete="RESTRICT"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ProposedAction(UUIDPrimaryKey, TimestampMixin, Base):
    """Confirmation-gated requested change, distinct from applied farm state."""

    __tablename__ = "proposed_actions"
    __table_args__ = (
        CheckConstraint(
            "source_module IN ('m2', 'm3', 'm4', 'm5', 'm6')",
            name="ck_proposed_actions_source_module",
        ),
        CheckConstraint(
            "status IN ('draft', 'awaiting_confirmation', 'confirmed', 'applied', "
            "'rejected', 'expired', 'conflict', 'failed')",
            name="ck_proposed_actions_status",
        ),
        CheckConstraint("version > 0", name="ck_proposed_actions_version_positive"),
        CheckConstraint("expires_at > created_at", name="ck_proposed_actions_expiry"),
        ForeignKeyConstraint(
            ["farmland_id", "farmer_id"],
            ["farmlands.id", "farmlands.farmer_id"],
            name="fk_proposed_actions_farmland_owner",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["season_id", "farmland_id"],
            ["seasons.id", "seasons.farmland_id"],
            name="fk_proposed_actions_season_farmland",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "farmer_id", name="uq_proposed_actions_id_farmer"),
        Index("ix_proposed_actions_farmer_status_expiry", "farmer_id", "status", "expires_at"),
        Index("ix_proposed_actions_farmland_created", "farmland_id", "created_at"),
    )

    farmer_id: Mapped[UUID] = mapped_column(nullable=False)
    farmland_id: Mapped[UUID] = mapped_column(nullable=False)
    season_id: Mapped[UUID | None] = mapped_column()
    source_module: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(28), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    contract_version: Mapped[str] = mapped_column(String(24), nullable=False)
    preconditions: Mapped[list] = mapped_column(JSONB, nullable=False)
    task_diff: Mapped[dict] = mapped_column(JSONB, nullable=False)
    required_consent_purposes: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ActionReceipt(UUIDPrimaryKey, Base):
    """Durable idempotency response for confirmation attempts."""

    __tablename__ = "action_receipts"
    __table_args__ = (
        CheckConstraint("action_version > 0", name="ck_action_receipts_version_positive"),
        CheckConstraint(
            "status IN ('applied', 'rejected', 'conflict', 'failed')",
            name="ck_action_receipts_status",
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= created_at",
            name="ck_action_receipts_completed_time",
        ),
        ForeignKeyConstraint(
            ["action_id", "farmer_id"],
            ["proposed_actions.id", "proposed_actions.farmer_id"],
            name="fk_action_receipts_action_owner",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("farmer_id", "idempotency_key", name="uq_action_receipts_farmer_key"),
        Index("ix_action_receipts_action_created", "action_id", "created_at"),
        Index("ix_action_receipts_farmer_created", "farmer_id", "created_at"),
    )

    action_id: Mapped[UUID] = mapped_column(nullable=False)
    farmer_id: Mapped[UUID] = mapped_column(nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    action_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DeliveryOutbox(UUIDPrimaryKey, Base):
    """At-least-once delivery intent committed with its domain receipt."""

    __tablename__ = "delivery_outbox"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'leased', 'delivered', 'retryable_failure', 'permanent_failure')",
            name="ck_delivery_outbox_status",
        ),
        CheckConstraint("attempts >= 0", name="ck_delivery_outbox_attempts_nonnegative"),
        CheckConstraint(
            "lease_until IS NULL OR status = 'leased'",
            name="ck_delivery_outbox_lease_state",
        ),
        ForeignKeyConstraint(
            ["receipt_id"], ["action_receipts.id"],
            name="fk_delivery_outbox_receipt", ondelete="RESTRICT"
        ),
        UniqueConstraint("receipt_id", "event_type", name="uq_delivery_outbox_receipt_event"),
        UniqueConstraint("idempotency_key", name="uq_delivery_outbox_idempotency_key"),
        Index("ix_delivery_outbox_ready", "status", "available_at", "created_at"),
    )

    receipt_id: Mapped[UUID] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(220), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", server_default=text("'pending'"))
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
