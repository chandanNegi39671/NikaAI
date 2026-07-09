"""
backend/app/services/prediction.py
────────────────────────────────────
Production-ready YOLOv8 inference service for Nika AI.

Responsibilities:
  1. Verify the model weights file exists on disk (raises ModelNotFoundError).
  2. Load the YOLOv8 model from the local file exactly once (singleton pattern).
  3. Warm up the model with a dummy forward pass after loading.
  4. Validate uploaded images before inference.
  5. Run inference and return a fully typed PredictionResult.
  6. Emit structured log records at every lifecycle event.

Design (SOLID):
  Single Responsibility — each method has exactly one job.
  Open/Closed         — add MC Dropout in Sprint 4 without changing this API.
  Liskov              — PredictionResult is immutable; callers can trust its type.
  Interface Seg.      — load_model / warmup / validate_image / predict are distinct.
  Dependency Inv.     — depends on settings (interface), not on concrete paths.

Sprint 1 Scope:
  - Standard YOLOv8 single-pass inference (no MC Dropout).
  - MC Dropout uncertainty estimation is deferred to Sprint 4.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from app.core.config import settings
from app.core.logging import get_logger
from app.exceptions import (
    InvalidImageError,
    ModelLoadError,
    ModelNotFoundError,
    ModelNotLoadedError,
    PredictionError,
)

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Value Objects (immutable data carriers)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BoundingBox:
    """Pixel-space bounding box for one detection.

    Coordinates are floats at the original input image resolution.
    They are NOT normalised to [0, 1].

    Attributes:
        x1: Left edge pixel x-coordinate.
        y1: Top edge pixel y-coordinate.
        x2: Right edge pixel x-coordinate.
        y2: Bottom edge pixel y-coordinate.
    """

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        """Bounding box width in pixels."""
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """Bounding box height in pixels."""
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        """Bounding box area in square pixels."""
        return self.width * self.height

    def to_dict(self) -> dict[str, float]:
        """Serialise to a plain dict for JSON responses."""
        return {
            "x1": round(self.x1, 2),
            "y1": round(self.y1, 2),
            "x2": round(self.x2, 2),
            "y2": round(self.y2, 2),
        }


@dataclass(frozen=True)
class Detection:
    """A single confirmed defect detection.

    Attributes:
        defect:       Class name (e.g. ``"surface_crack"``).
        confidence:   Model confidence score in [0.0, 1.0].
        bounding_box: Pixel-space location at original image size.
    """

    defect: str
    confidence: float
    bounding_box: BoundingBox

    def to_dict(self) -> dict:
        """Serialise to a plain dict for JSON responses."""
        return {
            "defect": self.defect,
            "confidence": round(self.confidence, 4),
            "bounding_box": self.bounding_box.to_dict(),
        }


@dataclass
class PredictionResult:
    """The complete output of one inference call.

    Attributes:
        detections:        All detections above the confidence threshold,
                           sorted by confidence descending.
        inference_time_ms: Wall-clock inference duration in milliseconds.
        image_width:       Original image width in pixels.
        image_height:      Original image height in pixels.
    """

    detections: list[Detection] = field(default_factory=list)
    inference_time_ms: float = 0.0
    image_width: int = 0
    image_height: int = 0

    @property
    def defect_count(self) -> int:
        """Number of detected defects."""
        return len(self.detections)

    @property
    def has_defects(self) -> bool:
        """True when at least one defect was detected."""
        return self.defect_count > 0

    def to_dict(self) -> dict:
        """Serialise to a plain dict for JSON API responses."""
        return {
            "success": True,
            "detections": [d.to_dict() for d in self.detections],
            "inference_time_ms": round(self.inference_time_ms, 2),
            "image_width": self.image_width,
            "image_height": self.image_height,
        }


# ─────────────────────────────────────────────────────────────────────────────
# PredictionService
# ─────────────────────────────────────────────────────────────────────────────


class PredictionService:
    """Manages the full lifecycle of the YOLOv8 model.

    Instantiate once at module level. Call ``load_model()`` once at application
    startup inside the FastAPI lifespan handler. Then call ``predict()`` per
    request.

    Attributes are private; interact only through public methods.

    Thread-Safety:
        YOLOv8 inference is CPU/GPU-bound. For Sprint 1 (single-image HTTP
        uploads) synchronous calls are sufficient. Sprint 2 (WebSocket) will
        wrap ``predict()`` in ``asyncio.run_in_executor``.
    """

    def __init__(self) -> None:
        # Private state — do not access from outside the class
        self._model: object | None = None  # ultralytics.YOLO instance
        self._model_path: Path = settings.model_path
        self._confidence: float = settings.confidence_threshold
        self._is_loaded: bool = False

    # ── Public lifecycle API ───────────────────────────────────────────────────

    def load_model(self) -> None:
        """Verify the weights file exists and load the YOLOv8 model into memory.

        Must be called once during application startup. Safe to call again —
        subsequent calls are a no-op when the model is already loaded.

        Raises:
            ModelNotFoundError: If ``settings.model_path`` does not exist on disk.
            ModelLoadError:     If ultralytics fails to parse the weights file.
        """
        if self._is_loaded:
            logger.info(
                "load_model() called but model is already loaded — skipping.",
                extra={"path": str(self._model_path)},
            )
            return

        self._assert_model_file_exists()
        self._load_weights()

    def switch_model(self, new_model_path: Path) -> None:
        """Switch the active model weights dynamically."""
        logger.info(f"Switching active YOLOv8 model to: {new_model_path}")
        self._model_path = new_model_path
        self._is_loaded = False
        self.load_model()
        self.warmup()

    def warmup(self) -> None:
        """Run a dummy forward pass to pre-compile the PyTorch model graph.

        Must be called after ``load_model()``. The warmup pass forces PyTorch
        to JIT-compile and cache the computation graph so the first real
        inference request is not penalised by compilation overhead.

        The warmup image is a black RGB image of size
        ``settings.warmup_image_size`` (default 640×640).

        Raises:
            ModelNotLoadedError: If called before ``load_model()``.
            PredictionError:     If the warmup forward pass itself fails.
        """
        if not self._is_loaded:
            raise ModelNotLoadedError()

        width, height = settings.warmup_image_size
        logger.info(
            "Running model warmup pass.",
            extra={"warmup_size": f"{width}x{height}"},
        )

        dummy_image: np.ndarray = np.zeros((height, width, 3), dtype=np.uint8)

        try:
            self._model.predict(
                source=dummy_image,
                conf=self._confidence,
                verbose=False,
            )
        except Exception as exc:
            raise PredictionError(reason=f"Warmup forward pass failed: {exc}") from exc

        logger.info("Model warmup complete. Service is ready.")

    def validate_image(self, image: Image.Image, size_bytes: int) -> None:
        """Validate a PIL Image before running inference.

        Checks applied (in order):
          1. File size ≤ ``settings.max_image_bytes``
          2. PIL format is in ``settings.allowed_image_formats``
          3. Image dimensions ≥ ``settings.min_image_dimension`` on both axes

        Args:
            image:      The decoded PIL Image to validate.
            size_bytes: The raw byte-length of the original uploaded file.

        Raises:
            InvalidImageError: On any validation failure with a descriptive message.
        """
        self._check_file_size(size_bytes)
        self._check_image_format(image)
        self._check_image_dimensions(image)

    def predict(self, image: Image.Image) -> PredictionResult:
        """Run YOLOv8 inference on a decoded PIL Image.

        The image must already be validated (call ``validate_image()`` first
        in the request handler, or trust that the API layer does so).

        Args:
            image: A PIL ``Image.Image`` object in any mode — converted to RGB
                   internally before inference.

        Returns:
            ``PredictionResult`` with all detections above the confidence
            threshold, sorted by confidence descending.

        Raises:
            ModelNotLoadedError: If ``load_model()`` was not called.
            PredictionError:     If the YOLOv8 forward pass fails at runtime.
        """
        if not self._is_loaded:
            raise ModelNotLoadedError()

        rgb_image: Image.Image = image.convert("RGB")
        img_w, img_h = rgb_image.size

        logger.debug(
            "Starting inference.",
            extra={"width": img_w, "height": img_h},
        )

        raw_results, inference_ms = self._run_forward_pass(rgb_image)
        detections = self._parse_results(raw_results)

        logger.info(
            "Inference complete.",
            extra={
                "num_detections": len(detections),
                "inference_ms": round(inference_ms, 2),
                "classes_found": [d.defect for d in detections],
            },
        )

        return PredictionResult(
            detections=detections,
            inference_time_ms=inference_ms,
            image_width=img_w,
            image_height=img_h,
        )

    # ── Diagnostic properties ─────────────────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        """True when the model is loaded and ready for inference."""
        return self._is_loaded

    @property
    def class_names(self) -> list[str]:
        """All defect class names the model was trained on.

        Returns an empty list if the model is not yet loaded.
        """
        if self._model is None:
            return []
        return list(self._model.names.values())

    # ── Private implementation methods ────────────────────────────────────────

    def _assert_model_file_exists(self) -> None:
        """Raise ModelNotFoundError if the weights file is missing.

        Raises:
            ModelNotFoundError: If the file does not exist.
        """
        if not self._model_path.exists():
            logger.error(
                "Model weights file not found.",
                extra={"expected_path": str(self._model_path)},
            )
            raise ModelNotFoundError(path=self._model_path)

        logger.info(
            "Model weights file found.",
            extra={"path": str(self._model_path)},
        )

    def _load_weights(self) -> None:
        """Load the YOLOv8 model from the local .pt file.

        Raises:
            ModelLoadError: If ultralytics cannot parse the file.
        """
        logger.info(
            "Loading YOLOv8 model into memory.",
            extra={"path": str(self._model_path)},
        )

        try:
            from ultralytics import YOLO  # deferred import — keeps startup fast

            self._model = YOLO(str(self._model_path))
            self._is_loaded = True

        except Exception as exc:
            logger.error(
                "Failed to load YOLOv8 model.",
                extra={"path": str(self._model_path), "error": str(exc)},
            )
            raise ModelLoadError(path=self._model_path, reason=exc) from exc

        logger.info(
            "YOLOv8 model loaded successfully.",
            extra={
                "num_classes": len(self.class_names),
                "classes": self.class_names,
                "confidence_threshold": self._confidence,
            },
        )

    def _check_file_size(self, size_bytes: int) -> None:
        """Raise InvalidImageError if the upload exceeds the size limit.

        Args:
            size_bytes: Raw byte-length of the uploaded file.

        Raises:
            InvalidImageError: If ``size_bytes`` > ``settings.max_image_bytes``.
        """
        limit = settings.max_image_bytes
        if size_bytes > limit:
            raise InvalidImageError(
                f"File size {size_bytes / 1_048_576:.1f} MB exceeds the "
                f"{limit / 1_048_576:.0f} MB limit."
            )

    def _check_image_format(self, image: Image.Image) -> None:
        """Raise InvalidImageError if the image format is not allowed.

        Args:
            image: Decoded PIL Image.

        Raises:
            InvalidImageError: If ``image.format`` is not in allowed formats.
        """
        allowed: list[str] = [
            fmt.split("/")[-1].upper() for fmt in settings.allowed_image_formats
        ]
        pil_format: str = (image.format or "UNKNOWN").upper()

        if pil_format not in allowed:
            raise InvalidImageError(
                f"Image format '{pil_format}' is not supported. "
                f"Accepted formats: {', '.join(allowed)}."
            )

    def _check_image_dimensions(self, image: Image.Image) -> None:
        """Raise InvalidImageError if the image is too small to inspect.

        Args:
            image: Decoded PIL Image.

        Raises:
            InvalidImageError: If either dimension < ``settings.min_image_dimension``.
        """
        min_dim: int = settings.min_image_dimension
        width, height = image.size

        if width < min_dim or height < min_dim:
            raise InvalidImageError(
                f"Image dimensions {width}×{height} px are too small. "
                f"Both sides must be at least {min_dim} px."
            )

    def _run_forward_pass(self, image: Image.Image) -> tuple[list, float]:
        """Execute the YOLOv8 model and return raw results + wall-clock time.

        Args:
            image: RGB PIL Image ready for inference.

        Returns:
            Tuple of (ultralytics Results list, inference_ms float).

        Raises:
            PredictionError: If the forward pass raises any exception.
        """
        t_start: float = time.perf_counter()

        try:
            results = self._model.predict(
                source=np.array(image),
                conf=self._confidence,
                verbose=False,  # suppress ultralytics stdout spam
                half=True,  # Enable FP16 half precision for performance
            )
        except Exception as exc:
            raise PredictionError(reason=exc) from exc

        inference_ms: float = (time.perf_counter() - t_start) * 1_000
        return results, inference_ms

    def _parse_results(self, results: list) -> list[Detection]:
        """Convert raw ultralytics results into a list of Detection objects.

        Sorts detections by confidence descending so the highest-confidence
        defect is always first.

        Args:
            results: The list returned by ``model.predict()``.

        Returns:
            List of ``Detection`` objects, sorted by confidence descending.
        """
        detections: list[Detection] = []

        if not results:
            return detections

        result = results[0]  # single image → single result object

        if result.boxes is None or len(result.boxes) == 0:
            return detections

        boxes = result.boxes

        for i in range(len(boxes)):
            xyxy = boxes.xyxy[i].cpu().numpy()
            confidence = float(boxes.conf[i].cpu().numpy())
            class_id = int(boxes.cls[i].cpu().numpy())
            class_name: str = result.names[class_id]

            detection = Detection(
                defect=class_name,
                confidence=confidence,
                bounding_box=BoundingBox(
                    x1=float(xyxy[0]),
                    y1=float(xyxy[1]),
                    x2=float(xyxy[2]),
                    y2=float(xyxy[3]),
                ),
            )
            detections.append(detection)

        # Highest confidence first
        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# Import this object in all other modules — do not instantiate PredictionService again.
# ─────────────────────────────────────────────────────────────────────────────

prediction_service: PredictionService = PredictionService()

# ── Background Inference Thread Pool & Status Tracker ──────────────────────────
import concurrent.futures
import uuid
from concurrent.futures import ThreadPoolExecutor
from enum import Enum


class InferenceJobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class InferenceJob:
    job_id: str
    status: InferenceJobStatus
    progress: float  # 0.0 to 1.0
    future: concurrent.futures.Future
    created_at: float
    started_at: float | None = None
    completed_at: float | None = None
    error: str | None = None


class PredictionExecutor:
    """Manages concurrent YOLOv8 inference requests via a background ThreadPoolExecutor."""

    def __init__(self, max_workers: int = 2) -> None:
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="yolo-worker"
        )
        self.jobs: dict[str, InferenceJob] = {}

    def submit(self, image: Image.Image) -> InferenceJob:
        """Submit a PIL image for background defect detection inference."""
        job_id = str(uuid.uuid4())
        created_at = time.time()

        def task_wrapper() -> PredictionResult:
            job = self.jobs.get(job_id)
            if job:
                job.status = InferenceJobStatus.PROCESSING
                job.progress = 0.5
                job.started_at = time.time()
            try:
                # Execute inference using singleton
                res = prediction_service.predict(image)
                if job:
                    job.status = InferenceJobStatus.COMPLETED
                    job.progress = 1.0
                    job.completed_at = time.time()
                return res
            except Exception as e:
                logger.error(
                    f"Background prediction failed for job {job_id}: {e}", exc_info=True
                )
                if job:
                    job.status = InferenceJobStatus.FAILED
                    job.progress = 1.0
                    job.error = str(e)
                    job.completed_at = time.time()
                raise e

        future = self.executor.submit(task_wrapper)
        job = InferenceJob(
            job_id=job_id,
            status=InferenceJobStatus.QUEUED,
            progress=0.0,
            future=future,
            created_at=created_at,
        )
        self.jobs[job_id] = job

        # Clean up history to prevent memory leak
        self._cleanup_jobs()
        return job

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job in the queue."""
        job = self.jobs.get(job_id)
        if not job:
            return False
        cancelled = job.future.cancel()
        if cancelled:
            job.status = InferenceJobStatus.CANCELLED
            job.progress = 1.0
        return cancelled

    def get_job_status(self, job_id: str) -> dict | None:
        """Query the current state and progress metadata of a background job."""
        job = self.jobs.get(job_id)
        if not job:
            return None
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "progress": job.progress,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error": job.error,
        }

    def _cleanup_jobs(self) -> None:
        """Purge records older than 1 hour."""
        now = time.time()
        cutoff = now - 3600
        self.jobs = {jid: j for jid, j in self.jobs.items() if j.created_at > cutoff}


prediction_executor: PredictionExecutor = PredictionExecutor(max_workers=2)
