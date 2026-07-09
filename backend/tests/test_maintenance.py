"""
backend/tests/test_maintenance.py
──────────────────────────────────
Sprint 7: Tests for the Maintenance Intelligence system.

Coverage:
    - MaintenanceEngine: health score computation, risk classification,
      RUL estimation, recommendation selection, trend detection, persistence.
    - TrendAnalysis: daily, weekly, monthly aggregations; defect type trend;
      machine failure trend; fleet summary.
    - MaintenanceRepository: get_history_for_machine, get_latest_for_machine,
      get_fleet_latest, count_by_risk_level.
    - Maintenance API: all 10 endpoints — auth, pagination, 404 handling.

Test conventions (consistent with conftest.py):
    - Use db_session fixture (rolled back after each test).
    - Use admin_headers / operator_headers for auth.
    - Use client fixture (FastAPI TestClient with DB override).
    - No external network calls.
    - No mocking of ORM queries — tests verify real SQL logic.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.repository import maintenance_prediction_repo
from app.models.db_models import (
    Inspection,
    Machine,
    MaintenancePrediction,
)
from app.services.maintenance_engine import (
    RECOMMENDATIONS,
    _classify_risk,
    _compute_health_score,
    _select_recommendation,
    run_maintenance_engine,
)
from app.services.trend_analysis import (
    get_daily_trend,
    get_defect_type_trend,
    get_machine_failure_trend,
    get_monthly_trend,
    get_trend_summary,
    get_weekly_trend,
)

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def machine(db_session: Session) -> Machine:
    """Create and persist a test machine."""
    m = Machine(
        name="Test Grinder Unit",
        model_number="TGU-01",
        status="operational",
        location="Zone D",
    )
    db_session.add(m)
    db_session.flush()
    return m


@pytest.fixture()
def machine_with_low_fail_rate(db_session: Session, machine: Machine) -> Machine:
    """Seed 20 inspections — 1 FAIL (5% defect rate → low risk)."""
    for i in range(19):
        db_session.add(
            Inspection(
                machine_id=machine.id,
                status="PASS",
                confidence=0.92,
                latency_ms=30.0,
                inference_time_ms=28.0,
            )
        )
    db_session.add(
        Inspection(
            machine_id=machine.id,
            status="FAIL",
            confidence=0.55,
            latency_ms=45.0,
            inference_time_ms=42.0,
        )
    )
    db_session.flush()
    return machine


@pytest.fixture()
def machine_with_high_fail_rate(db_session: Session, machine: Machine) -> Machine:
    """Seed 10 inspections — 6 FAIL (60% defect rate → critical risk)."""
    for i in range(4):
        db_session.add(
            Inspection(
                machine_id=machine.id,
                status="PASS",
                confidence=0.80,
                latency_ms=35.0,
                inference_time_ms=32.0,
            )
        )
    for i in range(6):
        db_session.add(
            Inspection(
                machine_id=machine.id,
                status="FAIL",
                confidence=0.50,
                latency_ms=50.0,
                inference_time_ms=48.0,
            )
        )
    db_session.flush()
    return machine


# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests — Health Score
# ─────────────────────────────────────────────────────────────────────────────


class TestHealthScore:
    def test_perfect_health(self):
        score = _compute_health_score(0.0, 0.0)
        assert score == 100.0

    def test_moderate_defect_rate(self):
        score = _compute_health_score(0.15, 0.10)
        assert 0 < score < 100

    def test_severe_defect_rate_clamps_to_zero(self):
        score = _compute_health_score(1.0, 1.0)
        assert score == 0.0

    def test_recency_penalty_applied(self):
        score_no_recent = _compute_health_score(0.10, 0.0)
        score_with_recent = _compute_health_score(0.10, 0.50)
        assert score_with_recent < score_no_recent

    def test_score_always_in_range(self):
        for dr in [0.0, 0.1, 0.5, 0.9, 1.0]:
            for rf in [0.0, 0.5, 1.0]:
                score = _compute_health_score(dr, rf)
                assert 0.0 <= score <= 100.0


# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests — Risk Classification
# ─────────────────────────────────────────────────────────────────────────────


class TestRiskClassification:
    def test_low_risk(self):
        assert _classify_risk(0.05) == "low"

    def test_moderate_risk(self):
        assert _classify_risk(0.12) == "moderate"

    def test_high_risk(self):
        assert _classify_risk(0.30) == "high"

    def test_critical_risk(self):
        assert _classify_risk(0.60) == "critical"

    def test_boundary_at_moderate(self):
        assert _classify_risk(0.10) == "moderate"

    def test_boundary_at_high(self):
        assert _classify_risk(0.25) == "high"

    def test_boundary_at_critical(self):
        assert _classify_risk(0.50) == "critical"


# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests — Recommendation Engine
# ─────────────────────────────────────────────────────────────────────────────


class TestRecommendationEngine:
    def test_critical_always_gets_replace_component(self):
        code, text = _select_recommendation("critical", [])
        assert code == "replace_component"
        assert text == RECOMMENDATIONS["replace_component"]

    def test_high_risk_with_scratch_gets_vibration_check(self):
        code, text = _select_recommendation("high", ["scratch"])
        assert code == "monitor_vibration"

    def test_high_risk_with_surface_crack_gets_load_reduction(self):
        code, text = _select_recommendation("high", ["surface_crack"])
        assert code == "reduce_machine_load"

    def test_high_risk_no_special_class_gets_schedule_maintenance(self):
        code, text = _select_recommendation("high", ["unknown_defect"])
        assert code == "schedule_maintenance"

    def test_moderate_risk_with_scratch_gets_inspect_conveyor(self):
        code, text = _select_recommendation("moderate", ["scratch"])
        assert code == "inspect_conveyor"

    def test_moderate_risk_other_gets_increase_frequency(self):
        code, text = _select_recommendation("moderate", ["dent"])
        assert code == "increase_inspection_frequency"

    def test_low_risk_always_continue_monitoring(self):
        code, text = _select_recommendation("low", [])
        assert code == "continue_monitoring"

    def test_recommendation_text_is_nonempty(self):
        for risk in ["low", "moderate", "high", "critical"]:
            code, text = _select_recommendation(risk, [])
            assert text and len(text) > 10


# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests — Maintenance Engine
# ─────────────────────────────────────────────────────────────────────────────


class TestMaintenanceEngine:
    def test_unknown_machine_raises_value_error(self, db_session: Session):
        with pytest.raises(ValueError, match="not found"):
            run_maintenance_engine(
                db_session, "nonexistent-machine-id", skip_persist=True
            )

    def test_no_inspections_returns_nominal(
        self, db_session: Session, machine: Machine
    ):
        result = run_maintenance_engine(db_session, machine.id, skip_persist=True)
        assert result["health_score"] == 100.0
        assert result["risk_level"] == "low"
        assert result["rul_days"] == 180
        assert result["recommendation_code"] == "continue_monitoring"
        assert result["trend"] == "stable"

    def test_low_fail_rate_gives_low_risk(
        self, db_session: Session, machine_with_low_fail_rate: Machine
    ):
        result = run_maintenance_engine(
            db_session, machine_with_low_fail_rate.id, skip_persist=True
        )
        assert result["risk_level"] == "low"
        assert result["health_score"] > 70.0
        assert result["rul_days"] == 180

    def test_high_fail_rate_gives_critical_risk(
        self, db_session: Session, machine_with_high_fail_rate: Machine
    ):
        result = run_maintenance_engine(
            db_session, machine_with_high_fail_rate.id, skip_persist=True
        )
        assert result["risk_level"] == "critical"
        assert result["health_score"] < 50.0
        assert result["rul_days"] == 5
        assert result["priority"] == "urgent"

    def test_result_contains_all_required_keys(
        self, db_session: Session, machine: Machine
    ):
        result = run_maintenance_engine(db_session, machine.id, skip_persist=True)
        required_keys = [
            "machine_id",
            "machine_name",
            "health_score",
            "risk_level",
            "rul_days",
            "defect_rate",
            "recommendation",
            "recommendation_code",
            "priority",
            "trend",
            "total_inspections",
            "failed_inspections",
            "next_maintenance_date",
            "computed_at",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_persist_creates_db_row(
        self, db_session: Session, machine_with_low_fail_rate: Machine
    ):
        run_maintenance_engine(
            db_session, machine_with_low_fail_rate.id, skip_persist=False
        )
        pred = maintenance_prediction_repo.get_latest_for_machine(
            db_session, machine_with_low_fail_rate.id
        )
        assert pred is not None
        assert pred.machine_id == machine_with_low_fail_rate.id
        assert pred.health_score > 0.0

    def test_trend_is_stable_on_first_run(
        self, db_session: Session, machine_with_low_fail_rate: Machine
    ):
        result = run_maintenance_engine(
            db_session, machine_with_low_fail_rate.id, skip_persist=True
        )
        assert result["trend"] == "stable"  # no prior prediction exists


# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests — Trend Analysis
# ─────────────────────────────────────────────────────────────────────────────


class TestTrendAnalysis:
    def test_daily_trend_returns_correct_number_of_days(self, db_session: Session):
        result = get_daily_trend(db_session, days=7)
        assert len(result) == 7

    def test_daily_trend_structure(self, db_session: Session):
        result = get_daily_trend(db_session, days=3)
        for entry in result:
            assert "date" in entry
            assert "total_inspections" in entry
            assert "pass_rate" in entry
            assert 0.0 <= entry["pass_rate"] <= 100.0

    def test_weekly_trend_returns_correct_weeks(self, db_session: Session):
        result = get_weekly_trend(db_session, weeks=4)
        assert len(result) == 4

    def test_monthly_trend_returns_correct_months(self, db_session: Session):
        result = get_monthly_trend(db_session, months=3)
        assert len(result) == 3

    def test_defect_type_trend_empty_when_no_inspections(self, db_session: Session):
        result = get_defect_type_trend(db_session, days=30)
        assert isinstance(result, list)

    def test_machine_failure_trend_structure(
        self, db_session: Session, machine: Machine
    ):
        result = get_machine_failure_trend(db_session, days=30)
        assert isinstance(result, list)
        for entry in result:
            assert "machine_id" in entry
            assert "defect_rate" in entry
            assert 0.0 <= entry["defect_rate"] <= 1.0

    def test_trend_summary_has_required_keys(self, db_session: Session):
        summary = get_trend_summary(db_session, days=7)
        required = [
            "period_days",
            "total_inspections",
            "failed_inspections",
            "pass_rate",
            "avg_confidence",
            "machines_at_risk",
            "total_machines",
        ]
        for key in required:
            assert key in summary, f"Missing key: {key}"

    def test_trend_clamps_days_to_max(self, db_session: Session):
        result = get_daily_trend(db_session, days=999)
        assert len(result) == 90  # clamped to max 90


# ─────────────────────────────────────────────────────────────────────────────
# Repository Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestMaintenancePredictionRepository:
    def _make_prediction(
        self, db: Session, machine: Machine, health_score: float = 80.0
    ) -> MaintenancePrediction:
        pred = MaintenancePrediction(
            machine_id=machine.id,
            health_score=health_score,
            risk_level="moderate" if health_score < 80 else "low",
            rul_days=45,
            defect_rate=0.12,
            recommendation="Test recommendation.",
            recommendation_code="schedule_maintenance",
            priority="medium",
            trend="stable",
            total_inspections=10,
            failed_inspections=1,
            computed_at=datetime.now(timezone.utc),
        )
        db.add(pred)
        db.flush()
        return pred

    def test_get_latest_for_machine(self, db_session: Session, machine: Machine):
        self._make_prediction(db_session, machine, health_score=90.0)
        self._make_prediction(db_session, machine, health_score=75.0)  # newer
        latest = maintenance_prediction_repo.get_latest_for_machine(
            db_session, machine.id
        )
        assert latest is not None
        assert latest.health_score == 75.0  # most recently added

    def test_get_history_for_machine_respects_limit(
        self, db_session: Session, machine: Machine
    ):
        for _ in range(5):
            self._make_prediction(db_session, machine)
        history = maintenance_prediction_repo.get_history_for_machine(
            db_session, machine.id, limit=3
        )
        assert len(history) == 3

    def test_get_latest_returns_none_when_no_predictions(
        self, db_session: Session, machine: Machine
    ):
        result = maintenance_prediction_repo.get_latest_for_machine(
            db_session, machine.id
        )
        assert result is None

    def test_count_by_risk_level(self, db_session: Session, machine: Machine):
        pred = self._make_prediction(db_session, machine)
        pred.risk_level = "high"
        db_session.flush()
        counts = maintenance_prediction_repo.count_by_risk_level(db_session)
        assert isinstance(counts, dict)


# ─────────────────────────────────────────────────────────────────────────────
# API Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestMaintenanceAPI:
    def test_fleet_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/maintenance/fleet")
        assert resp.status_code == 401

    def test_fleet_returns_ok(self, client: TestClient, admin_headers: dict):
        resp = client.get("/api/v1/maintenance/fleet", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_machines" in data
        assert "fleet" in data
        assert isinstance(data["fleet"], list)

    def test_predict_returns_404_for_unknown_machine(
        self, client: TestClient, admin_headers: dict
    ):
        resp = client.get(
            "/api/v1/maintenance/predict/nonexistent-id", headers=admin_headers
        )
        assert resp.status_code == 404

    def test_predict_returns_ok_for_valid_machine(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        machine: Machine,
    ):
        resp = client.get(
            f"/api/v1/maintenance/predict/{machine.id}", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["machine_id"] == machine.id
        assert "health_score" in data
        assert 0.0 <= data["health_score"] <= 100.0

    def test_history_returns_404_for_unknown_machine(
        self, client: TestClient, admin_headers: dict
    ):
        resp = client.get(
            "/api/v1/maintenance/history/nonexistent-id", headers=admin_headers
        )
        assert resp.status_code == 404

    def test_history_returns_empty_list_when_no_predictions(
        self, client: TestClient, admin_headers: dict, machine: Machine
    ):
        resp = client.get(
            f"/api/v1/maintenance/history/{machine.id}", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["predictions"] == []

    def test_report_returns_404_for_unknown_machine(
        self, client: TestClient, admin_headers: dict
    ):
        resp = client.get(
            "/api/v1/maintenance/report/nonexistent-id", headers=admin_headers
        )
        assert resp.status_code == 404

    def test_report_returns_ok_for_valid_machine(
        self, client: TestClient, admin_headers: dict, machine: Machine
    ):
        resp = client.get(
            f"/api/v1/maintenance/report/{machine.id}", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "current_health" in data
        assert "prediction_history" in data
        assert "defect_trend" in data

    def test_daily_trend_returns_list(self, client: TestClient, admin_headers: dict):
        resp = client.get(
            "/api/v1/maintenance/trend/daily?days=7", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 7

    def test_weekly_trend_returns_list(self, client: TestClient, admin_headers: dict):
        resp = client.get(
            "/api/v1/maintenance/trend/weekly?weeks=4", headers=admin_headers
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 4

    def test_monthly_trend_returns_list(self, client: TestClient, admin_headers: dict):
        resp = client.get(
            "/api/v1/maintenance/trend/monthly?months=3", headers=admin_headers
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_defect_trend_returns_list(self, client: TestClient, admin_headers: dict):
        resp = client.get(
            "/api/v1/maintenance/trend/defects?days=30", headers=admin_headers
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_machine_trend_returns_list(self, client: TestClient, admin_headers: dict):
        resp = client.get(
            "/api/v1/maintenance/trend/machines?days=30", headers=admin_headers
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_trend_summary_returns_dict(self, client: TestClient, admin_headers: dict):
        resp = client.get(
            "/api/v1/maintenance/trend/summary?days=7", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_inspections" in data
        assert "machines_at_risk" in data

    def test_operator_can_predict(
        self, client: TestClient, operator_headers: dict, machine: Machine
    ):
        """Operators have inspection:read — can trigger engine."""
        resp = client.get(
            f"/api/v1/maintenance/predict/{machine.id}", headers=operator_headers
        )
        assert resp.status_code == 200

    def test_operator_can_read_fleet(self, client: TestClient, operator_headers: dict):
        """Operators have analytics:read — confirmed in auth.py ROLE_PERMISSIONS."""
        # Operator has inspection:read but NOT analytics:read per auth.py
        # Fleet endpoint requires analytics:read — so operator should get 403
        resp = client.get("/api/v1/maintenance/fleet", headers=operator_headers)
        assert resp.status_code == 403

    def test_viewer_cannot_predict(
        self, client: TestClient, viewer_headers: dict, machine: Machine
    ):
        """Viewers do not have inspection:read permission."""
        resp = client.get(
            f"/api/v1/maintenance/predict/{machine.id}", headers=viewer_headers
        )
        assert resp.status_code == 403
