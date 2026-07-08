"""
backend/app/models/db_models.py
───────────────────────────────
SQLAlchemy models for Sprint 4.
Includes: User, Machine, Worker, Shift, Session, Inspection, Detection,
FactoryMemory, Report, AIExplanation, AnalyticsSnapshot, AuditLog.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from datetime import timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base


# Helper function to generate UUIDs
def generate_uuid() -> str:
    return str(uuid.uuid4())


class SoftDeleteMixin:
    """Mixin to support soft deletes on models."""
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    def delete(self):
        self.is_deleted = True


class TimestampMixin:
    """Mixin to automatically track created and updated times."""
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class User(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="operator", nullable=False)  # operator, admin, manager
    factory_id = Column(String(36), nullable=True, index=True)

    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User username={self.username} role={self.role}>"


class Machine(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "machines"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(100), nullable=False, index=True)
    model_number = Column(String(100), nullable=True)
    status = Column(String(50), default="operational", nullable=False)  # operational, maintenance, offline
    location = Column(String(100), nullable=True)
    factory_id = Column(String(36), nullable=True, index=True)

    inspections = relationship("Inspection", back_populates="machine")

    def __repr__(self) -> str:
        return f"<Machine name={self.name} status={self.status}>"


class Worker(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "workers"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(100), nullable=False, index=True)
    employee_code = Column(String(50), unique=True, nullable=False, index=True)
    role = Column(String(100), nullable=True)

    inspections = relationship("Inspection", back_populates="worker")
    shifts = relationship("Shift", back_populates="worker")

    def __repr__(self) -> str:
        return f"<Worker name={self.name} code={self.employee_code}>"


class Shift(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "shifts"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(50), nullable=False, index=True)  # Day, Evening, Night
    start_time = Column(String(50), nullable=False)  # e.g., "06:00:00"
    end_time = Column(String(50), nullable=False)    # e.g., "14:00:00"
    worker_id = Column(String(36), ForeignKey("workers.id"), nullable=True)

    worker = relationship("Worker", back_populates="shifts")
    inspections = relationship("Inspection", back_populates="shift")

    def __repr__(self) -> str:
        return f"<Shift name={self.name}>"


class Session(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "#NK-4821-AX"
    status = Column(String(50), default="active", nullable=False)  # active, completed

    inspections = relationship("Inspection", back_populates="session")

    def __repr__(self) -> str:
        return f"<Session session_id={self.session_id} status={self.status}>"


class Inspection(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "inspections"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=True, index=True)
    machine_id = Column(String(36), ForeignKey("machines.id"), nullable=True, index=True)
    worker_id = Column(String(36), ForeignKey("workers.id"), nullable=True, index=True)
    shift_id = Column(String(36), ForeignKey("shifts.id"), nullable=True, index=True)
    
    image_path = Column(String(512), nullable=True)
    original_image_name = Column(String(255), nullable=True)
    status = Column(String(20), default="PASS", nullable=False, index=True)  # PASS, FAIL
    latency_ms = Column(Float, default=0.0)
    inference_time_ms = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)  # average confidence of defects, or top detection confidence

    session = relationship("Session", back_populates="inspections")
    machine = relationship("Machine", back_populates="inspections")
    worker = relationship("Worker", back_populates="inspections")
    shift = relationship("Shift", back_populates="inspections")
    
    detections = relationship("Detection", back_populates="inspection", cascade="all, delete-orphan")
    explanation = relationship("AIExplanation", back_populates="inspection", uselist=False, cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="inspection", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Inspection id={self.id} status={self.status} confidence={self.confidence}>"


class Detection(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "detections"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    inspection_id = Column(String(36), ForeignKey("inspections.id"), nullable=False, index=True)
    defect_class = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)

    inspection = relationship("Inspection", back_populates="detections")

    def __repr__(self) -> str:
        return f"<Detection class={self.defect_class} confidence={self.confidence}>"


class FactoryMemory(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "factory_memories"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    defect_class = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    recurring_defect_pattern = Column(Text, nullable=True)  # descriptions of machines/shifts/defect characteristics
    recommended_action = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<FactoryMemory defect_class={self.defect_class}>"


class Report(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    inspection_id = Column(String(36), ForeignKey("inspections.id"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    format = Column(String(20), nullable=False, index=True)  # PDF, CSV, JSON

    inspection = relationship("Inspection", back_populates="reports")

    def __repr__(self) -> str:
        return f"<Report format={self.format} path={self.file_path}>"


class AIExplanation(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "ai_explanations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    inspection_id = Column(String(36), ForeignKey("inspections.id"), nullable=False, index=True, unique=True)
    gemma_explanation = Column(Text, nullable=True)
    trust_score = Column(Float, default=1.0)
    explanation_json = Column(Text, nullable=True)  # parsed key value components

    inspection = relationship("Inspection", back_populates="explanation")

    def __repr__(self) -> str:
        return f"<AIExplanation trust_score={self.trust_score}>"


class AnalyticsSnapshot(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "analytics_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    date = Column(String(20), nullable=False, index=True)  # YYYY-MM-DD
    total_inspections = Column(Integer, default=0)
    acceptance_rate = Column(Float, default=0.0)
    reject_rate = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)
    avg_latency_ms = Column(Float, default=0.0)
    most_frequent_defect = Column(String(100), nullable=True)
    top_risk_machine = Column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<AnalyticsSnapshot date={self.date} total={self.total_inspections}>"


class AuditLog(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., "delete_inspection", "run_predict"
    entity_type = Column(String(50), nullable=True)           # e.g., "inspection", "session"
    entity_id = Column(String(36), nullable=True)
    description = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Sprint 8 additions — rich audit trail columns (additive only)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    request_id = Column(String(64), nullable=True, index=True)

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} entity={self.entity_type}>"


# ─────────────────────────────────────────────────────────────────────────────
# MaintenancePrediction — Sprint 7: AI Manufacturing Intelligence
# ─────────────────────────────────────────────────────────────────────────────

class MaintenancePrediction(Base, SoftDeleteMixin, TimestampMixin):
    """Persisted result of the predictive maintenance engine for one machine at one point in time.

    Each call to the maintenance engine writes a new row, allowing historical
    trend analysis of health score, risk level, and recommended actions over time.

    Attributes:
        id:                   UUID primary key.
        machine_id:           FK reference to machines table (nullable for resilience).
        health_score:         Composite health score 0–100 (100 = perfect health).
        risk_level:           Categorical risk: "low" | "moderate" | "high" | "critical".
        rul_days:             Estimated remaining useful life in days.
        defect_rate:          Fraction of inspections that resulted in FAIL (0.0–1.0).
        recommendation:       Human-readable maintenance recommendation text.
        recommendation_code:  Machine-readable code, e.g. "schedule_maintenance".
        priority:             Action priority: "low" | "medium" | "high" | "urgent".
        trend:                Direction of health: "improving" | "stable" | "degrading".
        total_inspections:    Snapshot of total inspections at compute time.
        failed_inspections:   Snapshot of failed inspections at compute time.
        computed_at:          UTC timestamp when this prediction was computed.
    """

    __tablename__ = "maintenance_predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    machine_id = Column(String(36), ForeignKey("machines.id"), nullable=True, index=True)

    # Core health metrics
    health_score = Column(Float, nullable=False, default=100.0, index=True)
    risk_level = Column(String(20), nullable=False, default="low", index=True)
    rul_days = Column(Integer, nullable=False, default=180)
    defect_rate = Column(Float, nullable=False, default=0.0)

    # Recommendation
    recommendation = Column(Text, nullable=True)
    recommendation_code = Column(String(50), nullable=True, index=True)
    priority = Column(String(20), nullable=False, default="low", index=True)

    # Trend metadata
    trend = Column(String(20), nullable=False, default="stable")

    # Snapshot counters (denormalized for audit trail)
    total_inspections = Column(Integer, nullable=False, default=0)
    failed_inspections = Column(Integer, nullable=False, default=0)

    # Timestamp this prediction was generated (separate from created_at which is DB insert time)
    computed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationship
    machine = relationship("Machine", foreign_keys=[machine_id])

    def __repr__(self) -> str:
        return (
            f"<MaintenancePrediction machine_id={self.machine_id} "
            f"health={self.health_score} risk={self.risk_level}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 8: AI Manufacturing Intelligence
# ModelVersion, KnowledgeDocument, Conversation, ConversationMessage
# ─────────────────────────────────────────────────────────────────────────────

class ModelVersion(Base, SoftDeleteMixin, TimestampMixin):
    """Persisted metadata for each versioned YOLOv8 model checkpoint.

    Replaces the filesystem-only registry with a fully queryable DB record.
    Deployment status follows a strict lifecycle:
        training → validated → staging → production → archived
    At most one version should carry deployment_status='production' at a time.
    The service layer is responsible for enforcing this invariant.
    """

    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    version_name = Column(String(200), unique=True, nullable=False, index=True)
    file_path = Column(String(512), nullable=True)

    # Deployment lifecycle status
    deployment_status = Column(
        String(20), nullable=False, default="staging", index=True
    )  # training | validated | staging | production | archived

    # Performance metrics
    map_score = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    training_date = Column(DateTime(timezone=True), nullable=True)

    # Provenance & lineage
    dataset_name = Column(String(200), nullable=True)
    trained_by = Column(String(100), nullable=True)
    framework = Column(String(100), nullable=True)
    commit_hash = Column(String(64), nullable=True)
    artifact_path = Column(String(512), nullable=True)
    model_size_mb = Column(Float, nullable=True)
    parameter_count = Column(Integer, nullable=True)
    parent_version = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ModelVersion name={self.version_name} status={self.deployment_status}>"


class KnowledgeDocument(Base, SoftDeleteMixin, TimestampMixin):
    """Factory knowledge base document for the AI Copilot RAG pipeline.

    Sprint 8 uses keyword (SQL LIKE) retrieval.  A future VectorKnowledgeProvider
    will add semantic search without modifying this model.

    doc_type values: 'manual' | 'sop' | 'faq' | 'maintenance'
    tags is a comma-separated list for lightweight multi-tag filtering.
    """

    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    title = Column(String(300), nullable=False, index=True)
    content = Column(Text, nullable=False)
    doc_type = Column(String(50), nullable=False, index=True, default="manual")
    tags = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<KnowledgeDocument title={self.title} type={self.doc_type}>"


class Conversation(Base, SoftDeleteMixin, TimestampMixin):
    """Persistent conversation session for the AI Copilot.

    A session is keyed by `session_key` (stored client-side in localStorage).
    Messages are stored as normalized rows in ConversationMessage.
    `context_summary` is an optional running summary maintained by the LLM adapter
    to avoid token-window overflow on long sessions.
    """

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    session_key = Column(String(200), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    context_summary = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.timestamp",
    )

    def __repr__(self) -> str:
        return f"<Conversation session_key={self.session_key}>"


class ConversationMessage(Base, TimestampMixin):
    """Single normalized message in a Conversation.

    role values: 'user' | 'assistant'
    Does NOT inherit SoftDeleteMixin — messages are immutable audit records.
    """

    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    conversation_id = Column(
        String(36), ForeignKey("conversations.id"), nullable=False, index=True
    )
    role = Column(String(20), nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ConversationMessage role={self.role} conv={self.conversation_id}>"


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 7: Notification — omnichannel alert dispatch and acknowledgement
# ─────────────────────────────────────────────────────────────────────────────

class Notification(Base, SoftDeleteMixin, TimestampMixin):
    """Persisted record of a single notification dispatch attempt.

    One row per (event, channel) pair — a single alert broadcast to
    email + Slack + Teams produces three rows, each independently
    tracked for delivery status, retries, and acknowledgement. This is
    what makes "history" and "acknowledgement" real features instead of
    log lines that vanish on container restart.
    """
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)

    # What triggered this notification
    event_type = Column(String(50), nullable=False, index=True)   # e.g. "critical_defect", "machine_offline"
    priority = Column(String(20), nullable=False, default="normal", index=True)  # low | normal | high | critical
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    machine_id = Column(String(36), ForeignKey("machines.id"), nullable=True, index=True)
    metadata_json = Column(Text, nullable=True)  # arbitrary structured context, JSON-encoded

    # Delivery
    channel = Column(String(20), nullable=False, index=True)  # email | slack | teams | discord | sms | webhook
    recipient = Column(String(255), nullable=True)  # address / channel id / phone number, channel-dependent
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending | sent | failed
    attempts = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    # Escalation / acknowledgement
    requires_ack = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)

    machine = relationship("Machine")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])

    def __repr__(self) -> str:
        return f"<Notification channel={self.channel} status={self.status} event={self.event_type}>"
