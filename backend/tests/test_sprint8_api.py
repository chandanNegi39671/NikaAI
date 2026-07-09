"""
backend/tests/test_sprint8_api.py
─────────────────────────────────
Integration and API tests for Sprint 8 API endpoints:
- Model Registry CRUD & Swapping (/api/v1/models/*)
- AI Copilot upgraded assistant (/api/v1/assistant/*)
- Inference History query endpoints (/api/v1/inference/*)
- Compliance Audit Log query endpoints (/api/v1/audit/*)
- Visualization Engine coordinate reports (/api/v1/visualization/*)
- Role Based Access Control (RBAC) restrictions enforcement.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.db_models import (
    AuditLog,
    Conversation,
    ConversationMessage,
    Detection,
    Inspection,
    Machine,
    ModelVersion,
)


class TestModelRegistryAPI:
    """Tests for /api/v1/models/* endpoints."""

    def test_list_models(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        # Seed models
        m = ModelVersion(version_name="test_reg.pt", deployment_status="staging")
        db_session.add(m)
        db_session.flush()

        resp = client.get("/api/v1/models", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert len(data["models"]) >= 1
        names = [x["version_name"] for x in data["models"]]
        assert "test_reg.pt" in names

    def test_register_model(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        payload = {
            "version_name": "new_registered_model.pt",
            "file_path": "/path/to/weights.pt",
            "deployment_status": "staging",
            "map_score": 0.942,
            "notes": "Evaluation successful.",
        }
        resp = client.post(
            "/api/v1/models/register", json=payload, headers=admin_headers
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["version_name"] == "new_registered_model.pt"
        assert data["map_score"] == 0.942

        # Verify database insertion
        db_item = (
            db_session.query(ModelVersion)
            .filter(ModelVersion.version_name == "new_registered_model.pt")
            .first()
        )
        assert db_item is not None
        assert db_item.deployment_status == "staging"

    def test_switch_model(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        # Seed weights checkpoint
        m = ModelVersion(
            version_name="best.pt",
            file_path="app/models/best.pt",
            deployment_status="staging",
        )
        db_session.add(m)
        db_session.flush()

        # Switch weights
        resp = client.post(
            "/api/v1/models/switch?version_name=best.pt", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

        # Check DB status promoted
        db_session.expire_all()
        m_db = (
            db_session.query(ModelVersion)
            .filter(ModelVersion.version_name == "best.pt")
            .first()
        )
        assert m_db.deployment_status == "production"

    def test_switch_model_file_not_found(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        # Register a version that does not exist on disk
        m = ModelVersion(
            version_name="nonexistent.pt",
            file_path="/path/to/missing.pt",
            deployment_status="staging",
        )
        db_session.add(m)
        db_session.flush()

        resp = client.post(
            "/api/v1/models/switch?version_name=nonexistent.pt", headers=admin_headers
        )
        assert resp.status_code == 400
        assert "Failed to switch" in resp.json()["detail"]

    def test_update_lifecycle_status(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        m = ModelVersion(version_name="status_test.pt", deployment_status="training")
        db_session.add(m)
        db_session.flush()

        payload = {"version_name": "status_test.pt", "status": "validated"}
        resp = client.post("/api/v1/models/status", json=payload, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["deployment_status"] == "validated"


class TestAICopilotAPI:
    """Tests for /api/v1/assistant/* endpoints."""

    def test_ask_assistant_rule_based_response(
        self, client: TestClient, operator_headers: dict, db_session: Session
    ):
        payload = {
            "question": "What is the SOP for surface cracks?",
            "session_key": "test_sess_1",
        }
        resp = client.post(
            "/api/v1/assistant/ask", json=payload, headers=operator_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "sources" in data
        assert data["adapter"] == "rule_based"

        # Check conversation history insertion
        conv = (
            db_session.query(Conversation)
            .filter(Conversation.session_key == "test_sess_1")
            .first()
        )
        assert conv is not None
        messages = (
            db_session.query(ConversationMessage)
            .filter(ConversationMessage.conversation_id == conv.id)
            .all()
        )
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    def test_get_and_clear_assistant_history(
        self, client: TestClient, operator_headers: dict, db_session: Session
    ):
        # Create history directly
        conv = Conversation(session_key="test_sess_2")
        db_session.add(conv)
        db_session.flush()

        m1 = ConversationMessage(
            conversation_id=conv.id, role="user", content="Test prompt"
        )
        m2 = ConversationMessage(
            conversation_id=conv.id, role="assistant", content="Test answer"
        )
        db_session.add(m1)
        db_session.add(m2)
        db_session.flush()

        # Fetch history
        resp_get = client.get(
            "/api/v1/assistant/history/test_sess_2", headers=operator_headers
        )
        assert resp_get.status_code == 200
        data_get = resp_get.json()
        assert len(data_get) == 2
        assert data_get[0]["content"] == "Test prompt"

        # Clear history
        resp_del = client.delete(
            "/api/v1/assistant/history/test_sess_2", headers=operator_headers
        )
        assert resp_del.status_code == 200

        # Verify empty history
        db_session.expire_all()
        messages = (
            db_session.query(ConversationMessage)
            .filter(ConversationMessage.conversation_id == conv.id)
            .all()
        )
        assert len(messages) == 0

    def test_knowledge_base_management_admin_only(
        self,
        client: TestClient,
        admin_headers: dict,
        operator_headers: dict,
        db_session: Session,
    ):
        payload = {
            "title": "Buffer Guideline Manual",
            "content": "Perform guidelines using buffing pads.",
            "doc_type": "sop",
            "tags": "buffer,scratch",
        }

        # 1. Block operators from creating documents
        resp_block = client.post(
            "/api/v1/assistant/knowledge", json=payload, headers=operator_headers
        )
        assert resp_block.status_code == 403

        # 2. Allow admin to create documents
        resp_create = client.post(
            "/api/v1/assistant/knowledge", json=payload, headers=admin_headers
        )
        assert resp_create.status_code == 201
        assert resp_create.json()["title"] == "Buffer Guideline Manual"

        # 3. Retrieve knowledge docs list
        resp_list = client.get("/api/v1/assistant/knowledge", headers=operator_headers)
        assert resp_list.status_code == 200
        assert len(resp_list.json()) >= 1

        # 4. Search knowledge base
        resp_search = client.get(
            "/api/v1/assistant/knowledge/search?query=buffer", headers=operator_headers
        )
        assert resp_search.status_code == 200
        assert len(resp_search.json()) >= 1
        assert resp_search.json()[0]["title"] == "Buffer Guideline Manual"


class TestInferenceHistoryAPI:
    """Tests for /api/v1/inference/* endpoints."""

    def test_query_inference_history_filters(
        self, client: TestClient, operator_headers: dict, db_session: Session
    ):
        # Seed inspections and detections
        mach = Machine(name="Press C", model_number="P-003", status="operational")
        db_session.add(mach)
        db_session.flush()

        ins1 = Inspection(
            status="PASS", confidence=0.92, machine_id=mach.id, inference_time_ms=30.0
        )
        ins2 = Inspection(
            status="FAIL", confidence=0.88, machine_id=mach.id, inference_time_ms=35.0
        )
        db_session.add(ins1)
        db_session.add(ins2)
        db_session.flush()

        det = Detection(
            inspection_id=ins2.id,
            defect_class="surface_crack",
            confidence=0.88,
            x1=10,
            y1=10,
            x2=20,
            y2=20,
        )
        db_session.add(det)
        db_session.flush()

        # Query full list
        resp = client.get("/api/v1/inference/history", headers=operator_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 2

        # Filter by status
        resp_status = client.get(
            "/api/v1/inference/history?status=FAIL", headers=operator_headers
        )
        assert resp_status.status_code == 200
        assert resp_status.json()["total"] == 1
        assert resp_status.json()["results"][0]["id"] == ins2.id

        # Filter by defect category
        resp_defect = client.get(
            "/api/v1/inference/history?defect_class=crack", headers=operator_headers
        )
        assert resp_defect.status_code == 200
        assert resp_defect.json()["total"] == 1

        # Single inspection details retrieve
        resp_detail = client.get(
            f"/api/v1/inference/history/{ins2.id}", headers=operator_headers
        )
        assert resp_detail.status_code == 200
        assert resp_detail.json()["status"] == "FAIL"
        assert len(resp_detail.json()["detections"]) == 1


class TestComplianceAuditLogsAPI:
    """Tests for /api/v1/audit/* endpoints."""

    def test_query_audit_logs_rbac_filters(
        self,
        client: TestClient,
        admin_headers: dict,
        operator_headers: dict,
        db_session: Session,
    ):
        # Seed audit entries
        log1 = AuditLog(
            action="hot_swap_weights",
            entity_type="model",
            description="Swapped checkpoint.",
            ip_address="127.0.0.1",
            request_id="req_1",
        )
        db_session.add(log1)
        db_session.flush()

        # 1. Operators are forbidden to view compliance logs
        resp_op = client.get("/api/v1/audit", headers=operator_headers)
        assert resp_op.status_code == 403

        # 2. Admin is authorized
        resp_admin = client.get("/api/v1/audit", headers=admin_headers)
        assert resp_admin.status_code == 200
        assert resp_admin.json()["total"] >= 1

        # 3. Filter query
        resp_filter = client.get(
            "/api/v1/audit?request_id=req_1", headers=admin_headers
        )
        assert resp_filter.status_code == 200
        assert resp_filter.json()["total"] == 1
        assert resp_filter.json()["results"][0]["action"] == "hot_swap_weights"


class TestVisualizationEngineAPI:
    """Tests for /api/v1/visualization/* endpoints."""

    def test_get_visualization_report(
        self, client: TestClient, operator_headers: dict, db_session: Session
    ):
        ins = Inspection(status="FAIL", confidence=0.91, inference_time_ms=45.0)
        db_session.add(ins)
        db_session.flush()

        det = Detection(
            inspection_id=ins.id,
            defect_class="scratch",
            confidence=0.91,
            x1=5.0,
            y1=5.0,
            x2=15.0,
            y2=15.0,
        )
        db_session.add(det)
        db_session.flush()

        resp = client.get(
            f"/api/v1/visualization/report/{ins.id}", headers=operator_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["inspection_id"] == ins.id
        assert data["visualization_type"] == "simulated_explainability"
        assert len(data["heatmap_regions"]) == 1
        assert data["heatmap_regions"][0]["label"] == "scratch"
        assert "trust_score" in data
        assert "explanation" in data
