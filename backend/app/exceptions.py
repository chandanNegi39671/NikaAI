"""
backend/app/exceptions.py
──────────────────────────
Centralised custom exception hierarchy for Nika AI.

Design:
  - All application-level exceptions inherit from ``NikaAIError``.
  - This allows callers to catch the base class for a broad catch, or a
    specific subclass for precise error handling.
  - Exceptions are pure data carriers — no business logic lives here.
  - FastAPI exception handlers (added in the API layer) map these classes
    to specific HTTP status codes.

Exception Hierarchy:
    NikaAIError
    ├── ModelNotFoundError      model weights file missing from disk
    ├── ModelNotLoadedError     predict() called before load_model()
    ├── ModelLoadError          ultralytics failed to parse the .pt file
    ├── InvalidImageError       image failed format/size/dimension checks
    └── PredictionError         inference failed at runtime

Usage:
    from app.exceptions import ModelNotFoundError, InvalidImageError

    raise ModelNotFoundError(path="/app/models/best.pt")
    raise InvalidImageError("File type 'bmp' is not supported.")
"""

from __future__ import annotations

from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Base Exception
# ─────────────────────────────────────────────────────────────────────────────


class NikaAIError(Exception):
    """Base class for all Nika AI application exceptions.

    Catching ``NikaAIError`` provides a single broad catch for all
    application-level failures, distinct from third-party library exceptions.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: str = message

    def __str__(self) -> str:
        return f"[{type(self).__name__}] {self.message}"


# ─────────────────────────────────────────────────────────────────────────────
# Model Exceptions
# ─────────────────────────────────────────────────────────────────────────────


class ModelNotFoundError(NikaAIError):
    """Raised when the model weights file does not exist on disk.

    This is a configuration / deployment error. The operator must ensure
    ``best.pt`` is placed at the path specified in ``settings.model_path``
    before starting the server.

    Args:
        path: The path that was checked and found to be missing.

    Example:
        raise ModelNotFoundError(path=settings.model_path)
    """

    def __init__(self, path: Path | str) -> None:
        self.path: Path = Path(path)
        super().__init__(
            f"Model weights file not found at '{self.path}'. "
            f"Please place 'best.pt' at the configured model_path "
            f"and restart the server."
        )


class ModelNotLoadedError(NikaAIError):
    """Raised when ``predict()`` is called before ``load_model()`` has run.

    Indicates a programming error — the service was not initialised
    correctly in the application lifespan handler.

    Example:
        raise ModelNotLoadedError()
    """

    def __init__(self) -> None:
        super().__init__(
            "PredictionService.load_model() must be called during application "
            "startup before any call to predict(). "
            "Check the FastAPI lifespan handler in main.py."
        )


class ModelLoadError(NikaAIError):
    """Raised when ultralytics fails to load the .pt weights file.

    Wraps the underlying ultralytics / torch exception so callers only
    need to handle ``NikaAIError`` subclasses.

    Args:
        path:   The weights file path that failed to load.
        reason: The underlying exception or error message.

    Example:
        raise ModelLoadError(path=settings.model_path, reason=exc)
    """

    def __init__(self, path: Path | str, reason: Exception | str) -> None:
        self.path: Path = Path(path)
        self.reason: str = str(reason)
        super().__init__(
            f"Failed to load YOLOv8 model from '{self.path}': {self.reason}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Image Exceptions
# ─────────────────────────────────────────────────────────────────────────────


class InvalidImageError(NikaAIError):
    """Raised when an uploaded image fails validation checks.

    Covers: unsupported format, file too large, zero-dimension image,
    corrupted file, or non-image bytes.

    Args:
        reason: A human-readable description of why validation failed.

    Example:
        raise InvalidImageError("File type 'bmp' is not supported. Use JPEG or PNG.")
        raise InvalidImageError("Image file exceeds the 10 MB size limit.")
    """

    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid image: {reason}")


# ─────────────────────────────────────────────────────────────────────────────
# Inference Exceptions
# ─────────────────────────────────────────────────────────────────────────────


class PredictionError(NikaAIError):
    """Raised when YOLOv8 inference fails at runtime.

    This is distinct from ``InvalidImageError`` (bad input) and
    ``ModelLoadError`` (bad weights). ``PredictionError`` means the model
    is loaded and the image is valid, but the forward pass itself failed —
    e.g. due to a GPU OOM error or a corrupted intermediate tensor.

    Args:
        reason: The underlying exception or error message.

    Example:
        raise PredictionError(reason=exc)
    """

    def __init__(self, reason: Exception | str) -> None:
        self.reason: str = str(reason)
        super().__init__(f"Inference failed: {self.reason}")
