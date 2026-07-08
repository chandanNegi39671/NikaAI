"""
backend/app/core/repository.py
──────────────────────────────
Base Repository Pattern implementations for SQL Alchemy DB models.
"""

from typing import Generic, TypeVar, Type, List, Any
from sqlalchemy.orm import Session
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Generic base repository providing abstract database operations."""

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    def get(self, db: Session, id: Any) -> ModelType | None:
        """Fetch model by primary key id."""
        return db.query(self.model).filter(self.model.id == id, self.model.is_deleted == False).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Fetch multiple models with paging limit controls."""
        return db.query(self.model).filter(self.model.is_deleted == False).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: Any) -> ModelType:
        """Create and persist a model instance."""
        db.add(obj_in)
        db.commit()
        db.refresh(obj_in)
        return obj_in

    def remove(self, db: Session, id: Any) -> ModelType | None:
        """Perform soft delete by marking is_deleted flag true."""
        obj = db.query(self.model).filter(self.model.id == id).first()
        if obj:
            obj.is_deleted = True
            db.commit()
        return obj

# ── Concrete Repositories ─────────────────────────────────────────────────────

from app.models.db_models import (
    Inspection, Machine, Worker, FactoryMemory, MaintenancePrediction,
    ModelVersion, KnowledgeDocument, Conversation, ConversationMessage, AuditLog,
)

class InspectionRepository(BaseRepository[Inspection]):
    def __init__(self) -> None:
        super().__init__(Inspection)

    def list_with_filters(
        self, db: Session, status: str | None = None, machine_id: str | None = None, limit: int = 50, offset: int = 0
    ) -> List[Inspection]:
        """Custom repository query with filtering options."""
        q = db.query(self.model).filter(self.model.is_deleted == False)
        if status:
            q = q.filter(self.model.status == status)
        if machine_id:
            q = q.filter(self.model.machine_id == machine_id)
        return q.offset(offset).limit(limit).all()

    def list_with_full_filters(
        self,
        db: Session,
        machine_id: str | None = None,
        worker_id: str | None = None,
        shift_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        min_confidence: float | None = None,
        defect_class: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> tuple[List[Inspection], int]:
        """Full-featured filter query for Sprint 8 Inference History API.

        Returns (results, total_count) for pagination metadata.
        """
        from sqlalchemy import func, desc as sa_desc, asc as sa_asc
        from app.models.db_models import Detection

        q = db.query(self.model).filter(self.model.is_deleted == False)

        if machine_id:
            q = q.filter(self.model.machine_id == machine_id)
        if worker_id:
            q = q.filter(self.model.worker_id == worker_id)
        if shift_id:
            q = q.filter(self.model.shift_id == shift_id)
        if status:
            q = q.filter(self.model.status == status)
        if min_confidence is not None:
            q = q.filter(self.model.confidence >= min_confidence)
        if date_from:
            from datetime import datetime
            try:
                dt_from = datetime.fromisoformat(date_from)
                q = q.filter(self.model.created_at >= dt_from)
            except ValueError:
                pass
        if date_to:
            from datetime import datetime
            try:
                dt_to = datetime.fromisoformat(date_to)
                q = q.filter(self.model.created_at <= dt_to)
            except ValueError:
                pass
        if defect_class:
            q = q.join(Detection, Detection.inspection_id == self.model.id).filter(
                Detection.defect_class.ilike(f"%{defect_class}%"),
                Detection.is_deleted == False,
            )

        total = q.count()

        # Sorting
        sort_col = getattr(self.model, sort_by, self.model.created_at)
        if sort_dir == "asc":
            q = q.order_by(sa_asc(sort_col))
        else:
            q = q.order_by(sa_desc(sort_col))

        return q.offset(offset).limit(limit).all(), total

    def count_total(self, db: Session) -> int:
        return db.query(self.model).filter(self.model.is_deleted == False).count()

class MachineRepository(BaseRepository[Machine]):
    def __init__(self) -> None:
        super().__init__(Machine)

class WorkerRepository(BaseRepository[Worker]):
    def __init__(self) -> None:
        super().__init__(Worker)

class FactoryMemoryRepository(BaseRepository[FactoryMemory]):
    def __init__(self) -> None:
        super().__init__(FactoryMemory)


class MaintenancePredictionRepository(BaseRepository[MaintenancePrediction]):
    """Repository for persisted maintenance predictions.

    Provides history queries, trend lookups, and fleet-level summaries.
    All queries automatically exclude soft-deleted rows via BaseRepository.
    """

    def __init__(self) -> None:
        super().__init__(MaintenancePrediction)

    def get_history_for_machine(
        self,
        db: Session,
        machine_id: str,
        limit: int = 30,
        offset: int = 0,
    ) -> List[MaintenancePrediction]:
        """Return chronologically ordered health predictions for a single machine."""
        return (
            db.query(self.model)
            .filter(
                self.model.machine_id == machine_id,
                self.model.is_deleted == False,
            )
            .order_by(self.model.computed_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_latest_for_machine(
        self, db: Session, machine_id: str
    ) -> MaintenancePrediction | None:
        """Return the most recent prediction for a machine."""
        return (
            db.query(self.model)
            .filter(
                self.model.machine_id == machine_id,
                self.model.is_deleted == False,
            )
            .order_by(self.model.computed_at.desc(), self.model.id.desc())
            .first()
        )

    def get_fleet_latest(self, db: Session) -> List[MaintenancePrediction]:
        """Return the most recent prediction for every machine in the fleet.

        Uses a subquery to get the max computed_at per machine_id, then joins.
        """
        from sqlalchemy import func
        subq = (
            db.query(
                self.model.machine_id,
                func.max(self.model.computed_at).label("max_computed_at"),
            )
            .filter(self.model.is_deleted == False)
            .group_by(self.model.machine_id)
            .subquery()
        )
        return (
            db.query(self.model)
            .join(
                subq,
                (self.model.machine_id == subq.c.machine_id)
                & (self.model.computed_at == subq.c.max_computed_at),
            )
            .filter(self.model.is_deleted == False)
            .order_by(self.model.health_score.asc())  # worst health first
            .all()
        )

    def count_by_risk_level(self, db: Session) -> dict[str, int]:
        """Return count of active predictions grouped by risk_level."""
        from sqlalchemy import func
        rows = (
            db.query(self.model.risk_level, func.count(self.model.id))
            .filter(self.model.is_deleted == False)
            .group_by(self.model.risk_level)
            .all()
        )
        return {level: count for level, count in rows}


# ── Sprint 8 Repositories ─────────────────────────────────────────────────────

class ModelVersionRepository(BaseRepository[ModelVersion]):
    """Repository for AI model version registry.

    Enforces the single-production-version invariant: set_deployment_status
    to 'production' automatically archives any existing production model.
    """

    def __init__(self) -> None:
        super().__init__(ModelVersion)

    def get_production_model(self, db: Session) -> ModelVersion | None:
        """Return the currently active production model, if any."""
        return (
            db.query(self.model)
            .filter(
                self.model.deployment_status == "production",
                self.model.is_deleted == False,
            )
            .first()
        )

    def get_by_version_name(self, db: Session, version_name: str) -> ModelVersion | None:
        return (
            db.query(self.model)
            .filter(self.model.version_name == version_name, self.model.is_deleted == False)
            .first()
        )

    def set_deployment_status(
        self, db: Session, version_name: str, status: str
    ) -> ModelVersion | None:
        """Update deployment_status for a version.

        If status is 'production', all other versions currently in 'production'
        are automatically moved to 'archived' to preserve the invariant.
        """
        VALID_STATUSES = {"training", "validated", "staging", "production", "archived"}
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid deployment_status '{status}'. Must be one of {VALID_STATUSES}")

        if status == "production":
            # Archive previous production model
            db.query(self.model).filter(
                self.model.deployment_status == "production",
                self.model.is_deleted == False,
            ).update({"deployment_status": "archived"})

        target = self.get_by_version_name(db, version_name)
        if not target:
            return None
        target.deployment_status = status
        db.commit()
        db.refresh(target)
        return target

    def list_all(self, db: Session, limit: int = 100, offset: int = 0) -> List[ModelVersion]:
        return (
            db.query(self.model)
            .filter(self.model.is_deleted == False)
            .order_by(self.model.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )


class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    """Repository for copilot knowledge base documents.

    Implements keyword-based retrieval for Sprint 8.
    Extension point: a future VectorKnowledgeProvider will supply its own
    retrieval mechanism without modifying this repository.
    """

    def __init__(self) -> None:
        super().__init__(KnowledgeDocument)

    def search_by_keyword(
        self, db: Session, query: str, doc_type: str | None = None, limit: int = 5
    ) -> List[KnowledgeDocument]:
        """Full-text keyword search across title, content, and tags."""
        search = f"%{query}%"
        q = db.query(self.model).filter(
            self.model.is_deleted == False,
            self.model.is_active == True,
            (
                self.model.title.ilike(search)
                | self.model.content.ilike(search)
                | self.model.tags.ilike(search)
            ),
        )
        if doc_type:
            q = q.filter(self.model.doc_type == doc_type)
        return q.limit(limit).all()

    def list_active(
        self, db: Session, doc_type: str | None = None, limit: int = 50, offset: int = 0
    ) -> List[KnowledgeDocument]:
        q = db.query(self.model).filter(
            self.model.is_deleted == False, self.model.is_active == True
        )
        if doc_type:
            q = q.filter(self.model.doc_type == doc_type)
        return q.order_by(self.model.created_at.desc()).offset(offset).limit(limit).all()


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for persistent copilot conversation sessions."""

    def __init__(self) -> None:
        super().__init__(Conversation)

    def get_by_session_key(self, db: Session, session_key: str) -> Conversation | None:
        return (
            db.query(self.model)
            .filter(self.model.session_key == session_key, self.model.is_deleted == False)
            .first()
        )

    def get_or_create(
        self, db: Session, session_key: str, user_id: str | None = None
    ) -> Conversation:
        """Fetch existing conversation or create a new one atomically."""
        existing = self.get_by_session_key(db, session_key)
        if existing:
            return existing
        conv = Conversation(session_key=session_key, user_id=user_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv


class ConversationMessageRepository(BaseRepository[ConversationMessage]):
    """Repository for normalized conversation message rows."""

    def __init__(self) -> None:
        super().__init__(ConversationMessage)

    def get_messages_for_conversation(
        self, db: Session, conversation_id: str, limit: int = 50
    ) -> List[ConversationMessage]:
        return (
            db.query(self.model)
            .filter(self.model.conversation_id == conversation_id)
            .order_by(self.model.timestamp.asc())
            .limit(limit)
            .all()
        )

    def add_message(
        self, db: Session, conversation_id: str, role: str, content: str
    ) -> ConversationMessage:
        """Persist a new message row and return the saved instance."""
        from datetime import datetime, timezone
        msg = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    def delete_for_conversation(self, db: Session, conversation_id: str) -> int:
        """Hard-delete all messages in a conversation. Returns rows deleted."""
        count = db.query(self.model).filter(
            self.model.conversation_id == conversation_id
        ).delete()
        db.commit()
        return count


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for reading audit log records with full filter support."""

    def __init__(self) -> None:
        super().__init__(AuditLog)

    def list_with_filters(
        self,
        db: Session,
        date_from: str | None = None,
        date_to: str | None = None,
        user_id: str | None = None,
        action: str | None = None,
        ip_address: str | None = None,
        entity_type: str | None = None,
        request_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[AuditLog], int]:
        """Return filtered audit log entries and total count for pagination."""
        q = db.query(self.model).filter(self.model.is_deleted == False)

        if user_id:
            q = q.filter(self.model.user_id == user_id)
        if action:
            q = q.filter(self.model.action.ilike(f"%{action}%"))
        if ip_address:
            q = q.filter(self.model.ip_address.ilike(f"%{ip_address}%"))
        if entity_type:
            q = q.filter(self.model.entity_type == entity_type)
        if request_id:
            q = q.filter(self.model.request_id == request_id)
        if date_from:
            from datetime import datetime
            try:
                q = q.filter(self.model.created_at >= datetime.fromisoformat(date_from))
            except ValueError:
                pass
        if date_to:
            from datetime import datetime
            try:
                q = q.filter(self.model.created_at <= datetime.fromisoformat(date_to))
            except ValueError:
                pass

        total = q.count()
        results = q.order_by(self.model.created_at.desc()).offset(offset).limit(limit).all()
        return results, total


# ── Singleton instances ────────────────────────────────────────────────────────

inspection_repo = InspectionRepository()
machine_repo = MachineRepository()
worker_repo = WorkerRepository()
factory_memory_repo = FactoryMemoryRepository()
maintenance_prediction_repo = MaintenancePredictionRepository()

# Sprint 8 singletons
model_version_repo = ModelVersionRepository()
knowledge_document_repo = KnowledgeDocumentRepository()
conversation_repo = ConversationRepository()
conversation_message_repo = ConversationMessageRepository()
audit_log_repo = AuditLogRepository()