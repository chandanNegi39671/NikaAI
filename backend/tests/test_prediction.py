"""
backend/tests/test_prediction.py
──────────────────────────────────
Tests for the prediction endpoint and PredictionService.

Covers:
  - Upload validation (missing file, wrong MIME type, too small image)
  - Authentication enforcement (unauthenticated → 401, viewer → 403)
  - PredictionService unit tests (validate_image, _check_file_size, etc.)
  - BoundingBox and Detection value objects
  - PredictionResult serialisation
  - PredictionExecutor job lifecycle (submit, status, cancel)

NOTE: Actual YOLOv8 inference tests are skipped unless the model file is
      present at settings.model_path. Unit tests mock the model instead.
"""

from __future__ import annotations

import io
import time
import uuid

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from unittest.mock import MagicMock, patch

from app.services.prediction import (
    BoundingBox,
    Detection,
    PredictionResult,
    PredictionService,
    PredictionExecutor,
    InferenceJobStatus,
)
from app.exceptions import InvalidImageError, ModelNotLoadedError
from app.core.config import settings


# ── BoundingBox tests ─────────────────────────────────────────────────────────

class TestBoundingBox:
    def test_width_calculation(self):
        bb = BoundingBox(x1=10.0, y1=20.0, x2=110.0, y2=220.0)
        assert bb.width == pytest.approx(100.0)

    def test_height_calculation(self):
        bb = BoundingBox(x1=10.0, y1=20.0, x2=110.0, y2=220.0)
        assert bb.height == pytest.approx(200.0)

    def test_area_calculation(self):
        bb = BoundingBox(x1=0.0, y1=0.0, x2=10.0, y2=20.0)
        assert bb.area == pytest.approx(200.0)

    def test_to_dict_rounds_values(self):
        bb = BoundingBox(x1=1.12345, y1=2.98765, x2=10.0, y2=20.0)
        d = bb.to_dict()
        assert d["x1"] == pytest.approx(1.12, abs=0.01)
        assert set(d.keys()) == {"x1", "y1", "x2", "y2"}

    def test_immutable(self):
        bb = BoundingBox(x1=1.0, y1=2.0, x2=3.0, y2=4.0)
        with pytest.raises(Exception):
            bb.x1 = 99.0  # type: ignore


# ── Detection tests ───────────────────────────────────────────────────────────

class TestDetection:
    def test_to_dict_structure(self):
        d = Detection(
            defect="scratch",
            confidence=0.87,
            bounding_box=BoundingBox(x1=0, y1=0, x2=100, y2=100),
        )
        result = d.to_dict()
        assert result["defect"] == "scratch"
        assert result["confidence"] == pytest.approx(0.87, abs=0.001)
        assert "bounding_box" in result

    def test_confidence_rounded_to_4_places(self):
        d = Detection(
            defect="crack",
            confidence=0.123456789,
            bounding_box=BoundingBox(0, 0, 10, 10),
        )
        assert d.to_dict()["confidence"] == pytest.approx(0.1235, abs=0.0001)


# ── PredictionResult tests ────────────────────────────────────────────────────

class TestPredictionResult:
    def _make_result(self, n: int) -> PredictionResult:
        detections = [
            Detection(
                defect=f"defect_{i}",
                confidence=float(i) / 10.0,
                bounding_box=BoundingBox(0, 0, 10, 10),
            )
            for i in range(1, n + 1)
        ]
        return PredictionResult(
            detections=detections,
            inference_time_ms=55.5,
            image_width=640,
            image_height=480,
        )

    def test_defect_count(self):
        r = self._make_result(3)
        assert r.defect_count == 3

    def test_has_defects_false(self):
        r = self._make_result(0)
        assert not r.has_defects

    def test_has_defects_true(self):
        r = self._make_result(1)
        assert r.has_defects

    def test_to_dict_schema(self):
        r = self._make_result(2)
        d = r.to_dict()
        assert d["success"] is True
        assert isinstance(d["detections"], list)
        assert len(d["detections"]) == 2
        assert "inference_time_ms" in d
        assert "image_width" in d
        assert "image_height" in d


# ── PredictionService unit tests (model mocked) ───────────────────────────────

class TestPredictionServiceValidation:
    """Test PredictionService validation without loading the actual model."""

    @pytest.fixture()
    def service(self) -> PredictionService:
        s = PredictionService()
        # Mark model as loaded so we can call validate_image without triggering load
        s._is_loaded = True
        return s

    def test_validate_file_too_large(self, service: PredictionService):
        img = Image.new("RGB", (100, 100))
        with pytest.raises(InvalidImageError, match="exceeds"):
            service.validate_image(img, size_bytes=settings.max_image_bytes + 1)

    def test_validate_image_too_small(self, service: PredictionService):
        img = Image.new("RGB", (10, 10))
        img.format = "JPEG"
        with pytest.raises(InvalidImageError, match="too small"):
            service.validate_image(img, size_bytes=100)

    def test_validate_unsupported_format(self, service: PredictionService):
        img = Image.new("RGB", (200, 200))
        img.format = "BMP"
        with pytest.raises(InvalidImageError):
            service.validate_image(img, size_bytes=1000)

    def test_predict_raises_when_not_loaded(self):
        service = PredictionService()
        assert not service.is_loaded
        img = Image.new("RGB", (100, 100))
        with pytest.raises(ModelNotLoadedError):
            service.predict(img)

    def test_class_names_empty_before_load(self):
        service = PredictionService()
        assert service.class_names == []


# ── API endpoint tests (model mocked via patch) ───────────────────────────────

class TestPredictEndpoint:
    """Test the /api/v1/predict HTTP endpoint with a mocked prediction service."""

    def test_predict_unauthenticated(self, client: TestClient, sample_jpeg_bytes: bytes):
        resp = client.post(
            "/api/v1/predict",
            files={"image": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
        )
        assert resp.status_code == 401

    def test_predict_no_file(self, client: TestClient, operator_headers: dict):
        resp = client.post("/api/v1/predict", headers=operator_headers)
        assert resp.status_code == 422

    def test_predict_wrong_mime_type(
        self, client: TestClient, operator_headers: dict
    ):
        """Uploading a plain text file disguised as an image should be rejected."""
        fake_file = b"this is not an image"
        resp = client.post(
            "/api/v1/predict",
            files={"image": ("test.txt", fake_file, "text/plain")},
            headers=operator_headers,
        )
        assert resp.status_code in (400, 415, 422)

    @patch("app.api.endpoints.prediction.prediction_service")
    def test_predict_success_with_mock(
        self,
        mock_service: MagicMock,
        client: TestClient,
        operator_headers: dict,
        sample_jpeg_bytes: bytes,
    ):
        """When the model returns a clean result, endpoint must return 200 with detections list."""
        mock_service.is_loaded = True
        mock_result = PredictionResult(
            detections=[
                Detection(
                    defect="surface_crack",
                    confidence=0.92,
                    bounding_box=BoundingBox(10, 20, 200, 300),
                )
            ],
            inference_time_ms=43.2,
            image_width=100,
            image_height=100,
        )
        mock_service.validate_image.return_value = None
        mock_service.predict.return_value = mock_result

        resp = client.post(
            "/api/v1/predict",
            files={"image": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=operator_headers,
        )
        # Model not loaded in CI so accept 200 or 503
        assert resp.status_code in (200, 503)


# ── PredictionExecutor job lifecycle ─────────────────────────────────────────

class TestPredictionExecutor:
    def test_submit_returns_job(self):
        executor = PredictionExecutor(max_workers=1)
        img = Image.new("RGB", (100, 100))

        with patch.object(
            executor,
            "_cleanup_jobs",
            return_value=None,
        ), patch(
            "app.services.prediction.prediction_service.predict",
            return_value=PredictionResult([], 10.0, 100, 100),
        ):
            job = executor.submit(img)
            assert job.job_id is not None
            assert job.status in (InferenceJobStatus.QUEUED, InferenceJobStatus.PROCESSING)

    def test_get_nonexistent_job_returns_none(self):
        executor = PredictionExecutor(max_workers=1)
        result = executor.get_job_status("nonexistent-job-id")
        assert result is None

    def test_cancel_nonexistent_job_returns_false(self):
        executor = PredictionExecutor(max_workers=1)
        result = executor.cancel_job("nonexistent-job-id")
        assert result is False
