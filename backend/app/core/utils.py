"""
backend/app/core/utils.py
──────────────────────────
Reusable, stateless utility helpers for the Nika AI backend.

Rules:
  - Every function here must be pure (no side effects, no I/O).
  - No business logic — utilities operate on primitive types or stdlib types.
  - No imports from other app modules (prevents circular imports).

Contents:
  - image_from_bytes()   decode raw bytes to a PIL Image
  - format_ms()          format a float millisecond value for display
  - clamp()              clamp a numeric value to [min, max]
"""

from __future__ import annotations

import io
from typing import TypeVar

from PIL import Image, UnidentifiedImageError

from app.exceptions import InvalidImageError

# ─────────────────────────────────────────────────────────────────────────────
# Image helpers
# ─────────────────────────────────────────────────────────────────────────────


def image_from_bytes(data: bytes) -> Image.Image:
    """Decode raw bytes into a PIL RGB Image.

    Args:
        data: Raw binary content of an image file (JPEG, PNG, WebP, …).

    Returns:
        A PIL ``Image.Image`` object in RGB mode.

    Raises:
        InvalidImageError: If the bytes cannot be decoded as an image.

    Example:
        >>> with open("photo.jpg", "rb") as f:
        ...     img = image_from_bytes(f.read())
        >>> img.size
        (640, 480)
    """
    if not data:
        raise InvalidImageError("Image data is empty (0 bytes).")

    try:
        image = Image.open(io.BytesIO(data))
        return image.convert("RGB")
    except UnidentifiedImageError:
        raise InvalidImageError(
            "The uploaded file could not be identified as a valid image. "
            "Ensure the file is a JPEG, PNG, or WebP."
        )
    except Exception as exc:
        raise InvalidImageError(f"Failed to decode image: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# Numeric helpers
# ─────────────────────────────────────────────────────────────────────────────

_N = TypeVar("_N", int, float)


def clamp(value: _N, minimum: _N, maximum: _N) -> _N:
    """Clamp ``value`` to the inclusive range [``minimum``, ``maximum``].

    Args:
        value:   The value to clamp.
        minimum: Lower bound (inclusive).
        maximum: Upper bound (inclusive).

    Returns:
        The clamped value.

    Example:
        >>> clamp(1.5, 0.0, 1.0)
        1.0
        >>> clamp(-0.1, 0.0, 1.0)
        0.0
    """
    return max(minimum, min(value, maximum))


def format_ms(milliseconds: float, precision: int = 2) -> str:
    """Format a millisecond duration as a rounded string for logging/display.

    Args:
        milliseconds: Duration in milliseconds.
        precision:    Number of decimal places.

    Returns:
        A formatted string, e.g. ``"142.53 ms"``.

    Example:
        >>> format_ms(142.534)
        '142.53 ms'
    """
    return f"{milliseconds:.{precision}f} ms"
