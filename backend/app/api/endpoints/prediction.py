"""
backend/app/api/endpoints/prediction.py
─────────────────────────────────────────
POST /api/v1/predict — YOLOv8 defect detection endpoint.

Responsibilities (this file only):
  1. Accept a multipart/form-data upload with a single ``image`` field.
  2. Validate the upload at the HTTP layer (field present, MIME type allowed).
  3. Decode bytes → PIL Image without writing to disk.
  4. Delegate validation + inference to ``PredictionService`` (Module 1).
  5. Map the ``PredictionResult`` dataclass to the Pydantic response model.
  6. Return a fully typed JSON response.

What this file does NOT do:
  - Run the model          →  PredictionService._run_forward_pass()
  - Check image dimensions →  PredictionService.validate_image()
  - Build bounding boxes   →  PredictionService._parse_results()

Response shape (spec-compliant):
    {
        "success": true,
        "image": {"width": 1920, "height": 1080},
        "detections": [
            {
                "class": "surface_crack",
                "confidence": 0.94,
                "bounding_box": {"x1": 120.5, "y1": 80.0, "x2": 340.2, "y2": 260.7}
            }
        ],
        "inference_time_ms": 73.4
    }

MIME type allow-list (enforced before Pillow decodes):
    image/jpeg, image/jpg, image/png
"""

# from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import PermissionChecker
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.logging import get_logger
from app.exceptions import InvalidImageError, ModelNotLoadedError, PredictionError
from app.models.db_models import AIExplanation, Inspection, Machine, Shift, Worker
from app.models.db_models import Detection as DbDetection
from app.models.db_models import Session as DbSession
from app.services.gemma import generate_explanation
from app.services.prediction import PredictionResult, prediction_service

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Prediction"],
    dependencies=[Depends(PermissionChecker("inspection:write"))],
)

# ── Allowed MIME types at the HTTP boundary (before Pillow opens the file) ───
_ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/jpg", "image/png"}
)


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Response Models
# ─────────────────────────────────────────────────────────────────────────────


class BoundingBoxSchema(BaseModel):
    """Pixel-space bounding box coordinates at the original image resolution.

    Coordinates are **not** normalised to [0, 1].
    """

    x1: float = Field(description="Left edge x-coordinate (pixels).", examples=[120.5])
    y1: float = Field(description="Top edge y-coordinate (pixels).", examples=[80.0])
    x2: float = Field(description="Right edge x-coordinate (pixels).", examples=[340.2])
    y2: float = Field(
        description="Bottom edge y-coordinate (pixels).", examples=[260.7]
    )

    model_config = {
        "json_schema_extra": {
            "example": {"x1": 120.5, "y1": 80.0, "x2": 340.2, "y2": 260.7}
        }
    }


class DetectionSchema(BaseModel):
    """A single defect detection returned by the YOLOv8 model.

    Detections are sorted by ``confidence`` descending (highest-confidence
    defect first).
    """

    # NOTE: The spec requires the key ``"class"`` but ``class`` is a reserved
    # keyword in Python.  Pydantic's ``alias`` mechanism handles the rename
    # transparently — the Python attribute is ``defect_class``.
    defect_class: str = Field(
        alias="class",
        description="Defect class name as trained in the YOLOv8 model.",
        examples=["surface_crack"],
    )
    confidence: float = Field(
        description="Model confidence score in the range [0.0, 1.0].",
        ge=0.0,
        le=1.0,
        examples=[0.94],
    )
    bounding_box: BoundingBoxSchema = Field(
        description="Pixel-space bounding box at the original image resolution."
    )

    model_config = {
        "populate_by_name": True,  # allow both alias and Python name
        "json_schema_extra": {
            "example": {
                "class": "surface_crack",
                "confidence": 0.94,
                "bounding_box": {"x1": 120.5, "y1": 80.0, "x2": 340.2, "y2": 260.7},
            }
        },
    }


class ImageDimensionsSchema(BaseModel):
    """Original image dimensions in pixels."""

    width: int = Field(description="Image width in pixels.", examples=[1920])
    height: int = Field(description="Image height in pixels.", examples=[1080])

    model_config = {"json_schema_extra": {"example": {"width": 1920, "height": 1080}}}


class PredictResponse(BaseModel):
    """Complete response returned by POST /api/v1/predict.

    ``detections`` is an empty list when no defects are found above the
    confidence threshold — it is **never** ``null``.
    """

    success: bool = Field(
        default=True,
        description="Always ``true`` on a 200 response.",
        examples=[True],
    )
    id: str | None = Field(
        default=None,
        description="The unique database ID of the inspection record.",
        examples=["insp_20260707_123456_abcd"],
    )
    image: ImageDimensionsSchema = Field(
        description="Dimensions of the uploaded image in pixels."
    )
    detections: list[DetectionSchema] = Field(
        description=(
            "All defect detections above the confidence threshold, "
            "sorted by confidence descending. Empty list when no defects found."
        )
    )
    inference_time_ms: float = Field(
        description="Wall-clock inference duration in milliseconds.",
        examples=[73.4],
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "success": True,
                "image": {"width": 1920, "height": 1080},
                "detections": [
                    {
                        "class": "surface_crack",
                        "confidence": 0.94,
                        "bounding_box": {
                            "x1": 120.5,
                            "y1": 80.0,
                            "x2": 340.2,
                            "y2": 260.7,
                        },
                    }
                ],
                "inference_time_ms": 73.4,
            }
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _validate_content_type(upload: UploadFile) -> None:
    """Reject uploads with an unsupported MIME type before reading bytes.

    This is the *first* validation gate — cheap and dependency-free.
    ``PredictionService.validate_image()`` provides a second gate based on
    the actual decoded PIL format, guarding against spoofed Content-Type headers.

    Args:
        upload: The incoming ``UploadFile`` object from FastAPI.

    Raises:
        HTTPException 415: If ``upload.content_type`` is not in the allow-list.
        HTTPException 400: If ``upload.content_type`` is missing entirely.
    """
    if not upload.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Content-Type for uploaded file. "
            "Expected one of: image/jpeg, image/png.",
        )

    if upload.content_type.lower() not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{upload.content_type}'. "
                f"Accepted types: image/jpeg, image/png."
            ),
        )


async def _read_image_bytes(upload: UploadFile) -> bytes:
    """Read the full upload body into memory.

    Args:
        upload: The incoming ``UploadFile`` object.

    Returns:
        Raw bytes of the uploaded file.

    Raises:
        HTTPException 400: If the upload body is empty.
    """
    raw: bytes = await upload.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty. Please provide a valid image.",
        )
    return raw


def _decode_pil_image(raw: bytes, filename: str) -> Image.Image:
    """Decode raw bytes into a PIL Image without writing to disk.

    Args:
        raw:      Raw bytes from the uploaded file.
        filename: Original filename (used only for error messages).

    Returns:
        An open :class:`PIL.Image.Image` instance.

    Raises:
        HTTPException 422: If Pillow cannot decode the bytes as an image.
    """
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()  # force full decode; catches truncated files
        return image
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"File '{filename}' could not be decoded as an image. "
                f"Ensure it is a valid, non-corrupted JPEG or PNG."
            ),
        )
    except Exception as exc:
        logger.warning(
            "Unexpected error while decoding image.",
            extra={"file_name": filename, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to open image '{filename}': {exc}",
        )


def _build_response(
    result: PredictionResult, inspection_id: str | None = None
) -> PredictResponse:
    """Map a ``PredictionResult`` dataclass to the ``PredictResponse`` schema.

    This function exists solely to keep the route handler clean and to make
    the mapping logic independently testable.

    Args:
        result: The ``PredictionResult`` returned by ``PredictionService.predict()``.
        inspection_id: The primary key of the saved database inspection record.

    Returns:
        A ``PredictResponse`` Pydantic model ready for serialisation.
    """
    detection_schemas = [
        DetectionSchema(
            defect_class=d.defect,  # maps Detection.defect → "class"
            confidence=round(d.confidence, 4),
            bounding_box=BoundingBoxSchema(
                x1=round(d.bounding_box.x1, 2),
                y1=round(d.bounding_box.y1, 2),
                x2=round(d.bounding_box.x2, 2),
                y2=round(d.bounding_box.y2, 2),
            ),
        )
        for d in result.detections
    ]

    return PredictResponse(
        success=True,
        id=inspection_id,
        image=ImageDimensionsSchema(
            width=result.image_width,
            height=result.image_height,
        ),
        detections=detection_schemas,
        inference_time_ms=round(result.inference_time_ms, 2),
    )


# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Defect detection",
    description=(
        "Upload a JPEG or PNG image to run YOLOv8 defect detection. "
        "The model returns all detected defects with class names, "
        "confidence scores, and pixel-space bounding boxes. "
        "\n\n**Accepted formats:** `image/jpeg`, `image/png`  \n"
        "**Max file size:** 10 MB  \n"
        "**Min image size:** 32 × 32 px"
    ),
    status_code=status.HTTP_200_OK,
    response_model_by_alias=True,
    responses={
        200: {
            "description": "Inference completed successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "image": {"width": 1920, "height": 1080},
                        "detections": [
                            {
                                "class": "surface_crack",
                                "confidence": 0.94,
                                "bounding_box": {
                                    "x1": 120.5,
                                    "y1": 80.0,
                                    "x2": 340.2,
                                    "y2": 260.7,
                                },
                            }
                        ],
                        "inference_time_ms": 73.4,
                    }
                }
            },
        },
        400: {"description": "Missing image field or empty file body."},
        415: {"description": "Unsupported file type (not JPEG or PNG)."},
        422: {
            "description": (
                "Image validation failed: corrupted file, wrong format, "
                "file too large, or image dimensions too small."
            )
        },
        503: {"description": "Model not loaded — service not ready."},
    },
)
@limiter.limit("20/minute")
async def predict(
    request: Request,
    image: Annotated[
        UploadFile,
        File(
            description=(
                "Image file to analyse. " "Accepted: JPEG, JPG, PNG. Max size: 10 MB."
            )
        ),
    ],
    session_id: str | None = None,
    machine_id: str | None = None,
    worker_id: str | None = None,
    shift_id: str | None = None,
    db: Session = Depends(get_db),
) -> PredictResponse:
    """Run YOLOv8 defect detection on the uploaded image and persist results to database.

    **Steps performed by this endpoint:**
    1. Validate the Content-Type header (MIME allow-list).
    2. Read the upload body and reject empty files.
    3. Decode bytes into a PIL Image.
    4. Call ``PredictionService.validate_image()`` — size, format, dimensions.
    5. Call ``PredictionService.predict()`` — YOLOv8 forward pass.
    6. Save image to disk under static directory.
    7. Persist Session, Inspection, Detections, and AIExplanation to database.
    8. Return a ``PredictResponse``.
    """
    filename: str = image.filename or "upload"

    logger.info(
        "Prediction request received.",
        extra={
            "file_name": filename,
            "content_type": image.content_type,
            "session_id": session_id,
        },
    )

    # ── Gate 1: MIME type ─────────────────────────────────────────────────────
    _validate_content_type(image)

    # ── Gate 2: Read bytes ────────────────────────────────────────────────────
    raw: bytes = await _read_image_bytes(image)

    logger.debug(
        "Image bytes read.",
        extra={"file_name": filename, "size_bytes": len(raw)},
    )

    # ── Gate 3: Decode with Pillow ────────────────────────────────────────────
    pil_image: Image.Image = _decode_pil_image(raw, filename)

    # ── Gate 4: Domain validation (size, format, dimensions) ──────────────────
    try:
        prediction_service.validate_image(pil_image, size_bytes=len(raw))
    except InvalidImageError as exc:
        logger.warning(
            "Image failed domain validation.",
            extra={"file_name": filename, "reason": exc.message},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        )

    # ── Prediction Caching & Inference (Celery with fallback) ─────────────────
    import hashlib
    import json

    from app.core.redis import cache_get, cache_set

    image_hash = hashlib.sha256(raw).hexdigest()
    cache_key = f"prediction:hash:{image_hash}"
    cached_res = cache_get(cache_key)

    result = None
    if cached_res:
        logger.info(f"Prediction cache hit for hash: {image_hash}")
        try:
            from app.core.metrics import CACHE_HITS

            CACHE_HITS.labels(cache_type="prediction").inc()
        except Exception:
            pass
        try:
            res_dict = json.loads(cached_res)
            # Reconstruct PredictionResult object
            from app.services.prediction import BoundingBox, Detection, PredictionResult

            detections = []
            for d in res_dict.get("detections", []):
                bbox = d.get("bounding_box", {})
                detections.append(
                    Detection(
                        defect=d.get("defect"),
                        confidence=d.get("confidence"),
                        bounding_box=BoundingBox(
                            x1=bbox.get("x1"),
                            y1=bbox.get("y1"),
                            x2=bbox.get("x2"),
                            y2=bbox.get("y2"),
                        ),
                    )
                )
            result = PredictionResult(
                detections=detections,
                inference_time_ms=res_dict.get("inference_time_ms", 0.0),
                image_width=res_dict.get("image_width", 640),
                image_height=res_dict.get("image_height", 640),
            )
        except Exception as exc:
            logger.warning(f"Failed to parse cached prediction: {exc}")

    if not result:
        try:
            from app.core.metrics import CACHE_MISSES

            CACHE_MISSES.labels(cache_type="prediction").inc()
        except Exception:
            pass
        # Call Celery task for inference
        try:
            # Skip Celery for synchronous prediction (faster, no timeout issues)
            task_res = None

            if task_res and task_res.get("success") != False:
                from app.services.prediction import (
                    BoundingBox,
                    Detection,
                    PredictionResult,
                )

                detections = []
                for d in task_res.get("detections", []):
                    bbox = d.get("bounding_box", {})
                    detections.append(
                        Detection(
                            defect=d.get("defect"),
                            confidence=d.get("confidence"),
                            bounding_box=BoundingBox(
                                x1=bbox.get("x1"),
                                y1=bbox.get("y1"),
                                x2=bbox.get("x2"),
                                y2=bbox.get("y2"),
                            ),
                        )
                    )
                result = PredictionResult(
                    detections=detections,
                    inference_time_ms=task_res.get("inference_time_ms", 0.0),
                    image_width=task_res.get("image_width", 640),
                    image_height=task_res.get("image_height", 640),
                )
        except Exception as celery_exc:
            logger.warning(
                f"Celery inference failed or timed out, falling back to local service: {celery_exc}"
            )

    if not result:
        # Fallback to local prediction service
        try:
            result = prediction_service.predict(pil_image)
        except ModelNotLoadedError as exc:
            logger.error(
                "Model not loaded when predict() was called.",
                extra={"error": exc.message},
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model is not loaded. The service is not ready for inference.",
            )
        except PredictionError as exc:
            logger.error(
                "Inference failed.", extra={"file_name": filename, "error": exc.message}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference failed: {exc.reason}",
            )

    # Save to Redis cache
    try:
        cache_set(cache_key, json.dumps(result.to_dict()), ttl=86400)  # cache for 1 day
    except Exception as exc:
        logger.warning(f"Failed to cache prediction: {exc}")

    # Record YOLO latency metrics in Prometheus
    try:
        from app.core.metrics import YOLO_FPS, YOLO_INFERENCE_TIME

        YOLO_INFERENCE_TIME.observe(result.inference_time_ms / 1000.0)
        if result.inference_time_ms > 0:
            YOLO_FPS.set(1000.0 / result.inference_time_ms)
    except Exception:
        pass

    # ── Gate 6: Save Image using Storage Provider Adapter ─────────────────────
    ext = Path(filename).suffix or ".jpg"
    unique_filename = f"{uuid.uuid4()}{ext}"

    try:
        from app.core.storage import storage_provider

        db_image_path = storage_provider.save(raw, unique_filename)
    except Exception as exc:
        logger.error(f"Failed to save image using storage provider: {exc}")
        db_image_path = None

    # ── Gate 7: Database Persistence ──────────────────────────────────────────
    try:
        # Resolve/Create Session
        if session_id:
            db_session_row = (
                db.query(DbSession).filter(DbSession.session_id == session_id).first()
            )
            if not db_session_row:
                db_session_row = DbSession(session_id=session_id, status="active")
                db.add(db_session_row)
                db.commit()
                db.refresh(db_session_row)
        else:
            import random

            generated_id = (
                f"#NK-{random.randint(1000, 9999)}-{uuid.uuid4().hex[:2].upper()}"
            )
            db_session_row = DbSession(session_id=generated_id, status="active")
            db.add(db_session_row)
            db.commit()
            db.refresh(db_session_row)

        # Resolve machine, worker, shift defaults
        db_machine = None
        if machine_id:
            db_machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not db_machine:
            db_machine = db.query(Machine).first()

        db_worker = None
        if worker_id:
            db_worker = db.query(Worker).filter(Worker.id == worker_id).first()
        if not db_worker:
            db_worker = db.query(Worker).first()

        db_shift = None
        if shift_id:
            db_shift = db.query(Shift).filter(Shift.id == shift_id).first()
        if not db_shift:
            db_shift = db.query(Shift).first()

        is_pass = not result.has_defects
        status_str = "PASS" if is_pass else "FAIL"
        avg_confidence = 0.0
        if result.has_defects:
            avg_confidence = sum(d.confidence for d in result.detections) / len(
                result.detections
            )

        # Save Inspection
        db_inspection = Inspection(
            session_id=db_session_row.id if db_session_row else None,
            machine_id=db_machine.id if db_machine else None,
            worker_id=db_worker.id if db_worker else None,
            shift_id=db_shift.id if db_shift else None,
            image_path=db_image_path,
            original_image_name=filename,
            status=status_str,
            latency_ms=result.inference_time_ms,
            inference_time_ms=result.inference_time_ms,
            confidence=avg_confidence,
        )
        db.add(db_inspection)
        db.commit()
        db.refresh(db_inspection)

        # Save Detections
        for det in result.detections:
            db_det = DbDetection(
                inspection_id=db_inspection.id,
                defect_class=det.defect,
                confidence=det.confidence,
                x1=det.bounding_box.x1,
                y1=det.bounding_box.y1,
                x2=det.bounding_box.x2,
                y2=det.bounding_box.y2,
            )
            db.add(db_det)

        # Save AI Explanation (conditionally based on feature flag)
        from app.services.features import is_feature_enabled

        if result.has_defects:
            top_defect = result.detections[0]
            if is_feature_enabled("gemma_explanations"):
                explanation_res = generate_explanation(top_defect.defect)
                db_explanation = AIExplanation(
                    inspection_id=db_inspection.id,
                    gemma_explanation=explanation_res.explanation_text,
                    trust_score=explanation_res.trust_score,
                    explanation_json=explanation_res.explanation_json,
                )
                db.add(db_explanation)

            # Publish prediction completed event to the Event Bus
            try:
                from app.core.events import event_bus

                machine_name = db_machine.name if db_machine else "Unknown Machine"
                event_payload = {
                    "inspection_id": db_inspection.id,
                    "status": status_str,
                    "defect_type": top_defect.defect,
                    "confidence": top_defect.confidence,
                    "machine_name": machine_name,
                }
                event_bus.publish("prediction_finished", event_payload)
            except Exception as ev_exc:
                logger.warning(f"Failed to publish event to EventBus: {ev_exc}")
        else:
            if is_feature_enabled("gemma_explanations"):
                explanation_res = generate_explanation("no_defect")
                db_explanation = AIExplanation(
                    inspection_id=db_inspection.id,
                    gemma_explanation="No defects detected. Part is within nominal quality tolerance.",
                    trust_score=1.0,
                    explanation_json=explanation_res.explanation_json,
                )
                db.add(db_explanation)

        db.commit()
        inspection_id = db_inspection.id
        logger.info(
            f"Persisted inspection to DB. ID: {inspection_id}, Status: {status_str}"
        )

        # Broadcast over WebSockets
        try:
            import asyncio

            from app.api.endpoints.websocket import manager

            ws_data = {
                "event": "new_inspection",
                "inspection": {
                    "id": inspection_id,
                    "status": status_str,
                    "confidence": avg_confidence,
                    "latency_ms": result.inference_time_ms,
                    "machine_id": machine_id,
                    "image_path": db_image_path,
                },
            }
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(manager.broadcast_global(ws_data))
                if machine_id:
                    loop.create_task(manager.broadcast_to_machine(machine_id, ws_data))
            except RuntimeError:
                pass  # No running event loop — skip WS broadcast
        except Exception as ws_exc:
            logger.warning(f"Failed to broadcast websocket notification: {ws_exc}")

    except Exception as db_exc:
        db.rollback()
        inspection_id = None
        logger.error(f"Failed to persist prediction results to database: {db_exc}")

    # ── Build and return response ──────────────────────────────────────────────
    response = _build_response(result, inspection_id=inspection_id)

    logger.info(
        "Prediction response ready.",
        extra={
            "file_name": filename,
            "num_detections": len(result.detections),
            "inference_ms": result.inference_time_ms,
        },
    )

    return response
