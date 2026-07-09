"""
backend/tests/test_sprint8_models.py
───────────────────────────────────
Unit and repository tests for Sprint 8 database models:
- ModelVersion (lifecycle status management, metadata validation)
- KnowledgeDocument (active status, keyword retrieval)
- Conversation & ConversationMessage (persistent chat sessions)
- AuditLog (richer compliance columns)
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.core.repository import (
    audit_log_repo,
    conversation_message_repo,
    conversation_repo,
    knowledge_document_repo,
    model_version_repo,
)
from app.models.db_models import (
    AuditLog,
    KnowledgeDocument,
    ModelVersion,
)


class TestModelVersionRepository:
    def test_create_and_fetch_model_version(self, db_session: Session):
        version = ModelVersion(
            version_name="test_model_v1.pt",
            file_path="/models/registry/test_model_v1.pt",
            deployment_status="validated",
            map_score=0.925,
            precision=0.910,
            recall=0.895,
            dataset_name="demo_dataset",
            trained_by="Staff Arch",
            framework="YOLOv8",
            commit_hash="abc12345",
            model_size_mb=42.5,
            parameter_count=3200000,
            notes="Evaluated successfully.",
        )
        created = model_version_repo.create(db_session, version)

        assert created.id is not None
        assert created.version_name == "test_model_v1.pt"
        assert created.deployment_status == "validated"
        assert created.map_score == 0.925
        assert created.precision == 0.910
        assert created.recall == 0.895
        assert created.dataset_name == "demo_dataset"
        assert created.trained_by == "Staff Arch"
        assert created.framework == "YOLOv8"
        assert created.commit_hash == "abc12345"
        assert created.model_size_mb == 42.5
        assert created.parameter_count == 3200000
        assert created.notes == "Evaluated successfully."
        assert created.is_deleted is False

        fetched = model_version_repo.get(db_session, created.id)
        assert fetched is not None
        assert fetched.version_name == "test_model_v1.pt"

    def test_single_production_version_invariant(self, db_session: Session):
        # 1. Create two models in staging
        m1 = ModelVersion(version_name="model1.pt", deployment_status="staging")
        m2 = ModelVersion(version_name="model2.pt", deployment_status="staging")
        model_version_repo.create(db_session, m1)
        model_version_repo.create(db_session, m2)

        # 2. Promote model1 to production
        model_version_repo.set_deployment_status(db_session, "model1.pt", "production")
        assert (
            model_version_repo.get_by_version_name(
                db_session, "model1.pt"
            ).deployment_status
            == "production"
        )
        assert (
            model_version_repo.get_production_model(db_session).version_name
            == "model1.pt"
        )

        # 3. Promote model2 to production (should automatically archive model1)
        model_version_repo.set_deployment_status(db_session, "model2.pt", "production")
        db_session.expire_all()  # clear SQLAlchemy session cache

        assert (
            model_version_repo.get_by_version_name(
                db_session, "model2.pt"
            ).deployment_status
            == "production"
        )
        assert (
            model_version_repo.get_by_version_name(
                db_session, "model1.pt"
            ).deployment_status
            == "archived"
        )
        assert (
            model_version_repo.get_production_model(db_session).version_name
            == "model2.pt"
        )

    def test_set_invalid_status_raises_value_error(self, db_session: Session):
        m = ModelVersion(version_name="temp.pt", deployment_status="staging")
        model_version_repo.create(db_session, m)

        with pytest.raises(ValueError) as exc:
            model_version_repo.set_deployment_status(
                db_session, "temp.pt", "invalid_status"
            )
        assert "invalid_status" in str(exc.value)


class TestKnowledgeDocumentRepository:
    def test_create_and_keyword_search(self, db_session: Session):
        doc1 = KnowledgeDocument(
            title="SOP for surface cracks",
            content="When surface cracks are detected on Guide Rails, CNC machines must be halted immediately.",
            doc_type="sop",
            tags="crack,rail,cnc",
            is_active=True,
        )
        doc2 = KnowledgeDocument(
            title="FAQ about scratches",
            content="Minor scratches can be buffed out if they are under 0.2mm in depth.",
            doc_type="faq",
            tags="scratch,buffing",
            is_active=True,
        )
        doc3 = KnowledgeDocument(
            title="Inactive guide",
            content="Old procedures for scratches.",
            doc_type="manual",
            tags="scratch,old",
            is_active=False,
        )
        knowledge_document_repo.create(db_session, doc1)
        knowledge_document_repo.create(db_session, doc2)
        knowledge_document_repo.create(db_session, doc3)

        # Search for 'crack'
        results_crack = knowledge_document_repo.search_by_keyword(db_session, "crack")
        assert len(results_crack) == 1
        assert results_crack[0].title == "SOP for surface cracks"

        # Search for 'scratch'
        results_scratch = knowledge_document_repo.search_by_keyword(
            db_session, "scratch"
        )
        assert len(results_scratch) == 1
        assert results_scratch[0].title == "FAQ about scratches"

        # Search with non-matching query
        results_empty = knowledge_document_repo.search_by_keyword(
            db_session, "missing_term"
        )
        assert len(results_empty) == 0


class TestConversationRepository:
    def test_get_or_create_session(self, db_session: Session):
        session_key = "test_conversation_session_123"
        conv = conversation_repo.get_or_create(db_session, session_key)
        assert conv.id is not None
        assert conv.session_key == session_key
        assert conv.is_deleted is False

        # Fetching again should return the existing one
        conv_second = conversation_repo.get_or_create(db_session, session_key)
        assert conv_second.id == conv.id

    def test_add_and_fetch_messages(self, db_session: Session):
        conv = conversation_repo.get_or_create(db_session, "session_key_abc")

        m1 = conversation_message_repo.add_message(
            db_session, conv.id, "user", "Hello copilot"
        )
        m2 = conversation_message_repo.add_message(
            db_session, conv.id, "assistant", "Hello! How can I assist you?"
        )

        assert m1.id is not None
        assert m1.role == "user"
        assert m1.content == "Hello copilot"
        assert m2.role == "assistant"
        assert m2.content == "Hello! How can I assist you?"

        messages = conversation_message_repo.get_messages_for_conversation(
            db_session, conv.id
        )
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

        # Delete messages for conversation
        deleted_count = conversation_message_repo.delete_for_conversation(
            db_session, conv.id
        )
        assert deleted_count == 2

        messages_after = conversation_message_repo.get_messages_for_conversation(
            db_session, conv.id
        )
        assert len(messages_after) == 0


class TestAuditLogExtendedRepository:
    def test_audit_log_extended_fields(self, db_session: Session):
        log = AuditLog(
            action="switch_model",
            entity_type="model",
            entity_id="model_id_123",
            description="Operator switched production weights.",
            ip_address="192.168.1.100",
            old_value="v1.pt",
            new_value="v2.pt",
            request_id="req_uuid_abc_123",
        )
        created = audit_log_repo.create(db_session, log)
        assert created.id is not None
        assert created.old_value == "v1.pt"
        assert created.new_value == "v2.pt"
        assert created.request_id == "req_uuid_abc_123"

        results, total = audit_log_repo.list_with_filters(
            db_session,
            action="switch_model",
            request_id="req_uuid_abc_123",
            entity_type="model",
        )
        assert total == 1
        assert len(results) == 1
        assert results[0].old_value == "v1.pt"
        assert results[0].new_value == "v2.pt"
