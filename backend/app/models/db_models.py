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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class User(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="operator", nullable=False)  # operator, admin, manager

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

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} entity={self.entity_type}>"
