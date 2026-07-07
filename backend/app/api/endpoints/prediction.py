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

from __future__ import annotations

import io
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.exceptions import InvalidImageError, ModelNotLoadedError, PredictionError
from app.services.prediction import PredictionResult, prediction_service

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Prediction"],
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
    y2: float = Field(description="Bottom edge y-coordinate (pixels).", examples=[260.7])

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
        "populate_by_name": True,   # allow both alias and Python name
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

    model_config = {
        "json_schema_extra": {"example": {"width": 1920, "height": 1080}}
    }


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
        image.load()   # force full decode; catches truncated files
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
            extra={"filename": filename, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to open image '{filename}': {exc}",
        )


def _build_response(result: PredictionResult) -> PredictResponse:
    """Map a ``PredictionResult`` dataclass to the ``PredictResponse`` schema.

    This function exists solely to keep the route handler clean and to make
    the mapping logic independently testable.

    Args:
        result: The ``PredictionResult`` returned by ``PredictionService.predict()``.

    Returns:
        A ``PredictResponse`` Pydantic model ready for serialisation.
    """
    detection_schemas = [
        DetectionSchema(
            defect_class=d.defect,              # maps Detection.defect → "class"
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
        image=ImageDimensionsSchema(
            width=result.image_width,
            height=result.image_height,
        ),
        detections=detection_schemas,
        inference_time_ms=round(result.inference_time_ms, 2),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Route
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
async def predict(
    image: Annotated[
        UploadFile,
        File(
            description=(
                "Image file to analyse. "
                "Accepted: JPEG, JPG, PNG. Max size: 10 MB."
            )
        ),
    ],
) -> PredictResponse:
    """Run YOLOv8 defect detection on the uploaded image.

    **Steps performed by this endpoint:**
    1. Validate the Content-Type header (MIME allow-list).
    2. Read the upload body and reject empty files.
    3. Decode bytes into a PIL Image (no temp files written to disk).
    4. Call ``PredictionService.validate_image()`` — size, format, dimensions.
    5. Call ``PredictionService.predict()`` — YOLOv8 forward pass.
    6. Return a ``PredictResponse`` with detections sorted by confidence.
    """
    filename: str = image.filename or "upload"

    # NOTE: image.size is None until bytes are read; log content_type only here.
    logger.info(
        "Prediction request received.",
        extra={
            "filename": filename,
            "content_type": image.content_type,
        },
    )

    # ── Gate 1: MIME type ─────────────────────────────────────────────────────
    _validate_content_type(image)

    # ── Gate 2: Read bytes ────────────────────────────────────────────────────
    raw: bytes = await _read_image_bytes(image)

    logger.debug(
        "Image bytes read.",
        extra={"filename": filename, "size_bytes": len(raw)},
    )

    # ── Gate 3: Decode with Pillow ────────────────────────────────────────────
    pil_image: Image.Image = _decode_pil_image(raw, filename)

    # ── Gate 4: Domain validation (size, format, dimensions) ──────────────────
    try:
        prediction_service.validate_image(pil_image, size_bytes=len(raw))
    except InvalidImageError as exc:
        logger.warning(
            "Image failed domain validation.",
            extra={"filename": filename, "reason": exc.message},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        )

    # ── Gate 5: Inference ─────────────────────────────────────────────────────
    try:
        result: PredictionResult = prediction_service.predict(pil_image)
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
            "Inference failed.",
            extra={"filename": filename, "error": exc.message},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {exc.reason}",
        )

    # ── Build and return response ──────────────────────────────────────────────
    response = _build_response(result)

    logger.info(
        "Prediction response ready.",
        extra={
            "filename": filename,
            "num_detections": len(result.detections),
            "inference_ms": result.inference_time_ms,
        },
    )

    return response
