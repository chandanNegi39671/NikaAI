"""
backend/app/core/upload.py
──────────────────────────
Enterprise-grade secure file upload pipeline.
"""

from __future__ import annotations

import io
import re
import uuid
from pathlib import Path
from typing import Set

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.core.logging import get_logger
from app.exceptions import InvalidImageError

logger = get_logger(__name__)

# Map MIME types to allowed extensions
MIME_TO_EXT = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
}


def allowed_file(filename: str, content_type: str) -> bool:
    """Validate that the file extension and MIME type match the whitelist.

    Prevents double extensions (e.g., file.png.exe) and verifies that the
    declared Content-Type matches the extension.
    """
    if not filename or not content_type:
        return False

    # 1. Prevent double extensions or malicious dots in filename
    # Check if there's more than one dot in the filename (excluding hidden files start dot)
    cleaned_name = Path(filename).name
    parts = cleaned_name.split(".")
    if len(parts) > 2:
        logger.warning(
            f"File upload rejected: Double extension detected in '{filename}'"
        )
        return False

    # 2. Extract extension and validate
    ext = Path(cleaned_name).suffix.lower()
    allowed_exts: Set[str] = set()
    for exts in MIME_TO_EXT.values():
        allowed_exts.update(exts)

    if ext not in allowed_exts:
        logger.warning(f"File upload rejected: Extension '{ext}' not in allowed list")
        return False

    # 3. Verify content type
    normalized_content_type = content_type.lower()
    if normalized_content_type not in settings.allowed_image_formats:
        logger.warning(f"File upload rejected: MIME type '{content_type}' not allowed")
        return False

    # 4. Verify extension matches the MIME type
    valid_exts_for_mime = MIME_TO_EXT.get(normalized_content_type, set())
    if ext not in valid_exts_for_mime:
        logger.warning(
            f"File upload rejected: Extension '{ext}' does not match MIME type '{content_type}'"
        )
        return False

    return True


def secure_filename(filename: str) -> str:
    """Sanitize the original filename to prevent directory traversal and execution.

    Strips directory paths and filters characters to be purely alphanumeric,
    dashes, underscores, or single dots.
    """
    # Extract only the base name to prevent directory traversal
    base_name = Path(filename).name

    # Separate name and extension
    name_part = Path(base_name).stem
    ext_part = Path(base_name).suffix

    # Keep only alphanumeric characters, underscores, and hyphens in the name part
    sanitized_name = re.sub(r"[^a-zA-Z0-9_\-]", "", name_part)

    # Clean the extension part to alphanumeric and check it's clean
    sanitized_ext = re.sub(r"[^a-zA-Z0-9.]", "", ext_part)

    if not sanitized_name:
        sanitized_name = "sanitized_upload"

    return f"{sanitized_name}{sanitized_ext}"


def validate_image(image_bytes: bytes) -> None:
    """Fully decode the image bytes using Pillow to verify structural integrity.

    Detects truncated images, execution payloads hidden in image headers,
    and size constraints.
    """
    # Check physical size limits
    if len(image_bytes) > settings.max_image_bytes:
        raise InvalidImageError(
            f"File size {len(image_bytes) / (1024 * 1024):.2f} MB exceeds the limit of "
            f"{settings.max_image_bytes / (1024 * 1024):.0f} MB."
        )

    try:
        # Load and verify structural integrity
        img_io = io.BytesIO(image_bytes)
        img = Image.open(img_io)
        img.verify()

        # Re-open for decoding check since verify() closes the file pointer
        img_io.seek(0)
        img = Image.open(img_io)
        img.load()  # Forces pixel loading to check for truncation/corruption

        # Verify minimum dimensions
        min_dim = settings.min_image_dimension
        if img.width < min_dim or img.height < min_dim:
            raise InvalidImageError(
                f"Image dimensions {img.width}x{img.height} are smaller than the minimum "
                f"required {min_dim}x{min_dim}."
            )

    except (UnidentifiedImageError, ValueError, TypeError, SyntaxError) as exc:
        logger.error(f"Image decoding verification failed: {exc}", exc_info=True)
        raise InvalidImageError("Uploaded file is not a valid, non-corrupted image.")


async def save_upload(upload_file: UploadFile, static_dir: Path) -> str:
    """Execute the full secure file upload pipeline.

    1. Validates filename extensions and content types.
    2. Reads the file content and validates the image structure.
    3. Generates a random UUID filename to prevent naming collisions and traversals.
    4. Writes the verified bytes to the secure static folder.
    5. Returns the virtual web path to the file.
    """
    orig_filename = upload_file.filename or "upload"
    content_type = upload_file.content_type or ""

    if not allowed_file(orig_filename, content_type):
        raise InvalidImageError(
            "File type or extension validation failed. Upload rejected."
        )

    # Read the file bytes
    try:
        image_bytes = await upload_file.read()
    except Exception as exc:
        logger.error(f"Failed to read upload file bytes: {exc}")
        raise InvalidImageError("Failed to read file content.")

    if not image_bytes:
        raise InvalidImageError("Uploaded file is empty.")

    # Validate image bytes integrity
    validate_image(image_bytes)

    # Generate unique UUID filename
    ext = Path(orig_filename).suffix.lower()
    unique_filename = f"{uuid.uuid4().hex}{ext}"

    # Resolve target directory securely
    uploads_dir = static_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    target_path = (uploads_dir / unique_filename).resolve()

    # Double-check path traversal protection
    if not str(target_path).startswith(str(uploads_dir.resolve())):
        logger.error(f"Path traversal attempt blocked: {target_path}")
        raise InvalidImageError("Invalid upload target path.")

    # Save the file to disk
    try:
        with open(target_path, "wb") as f:
            f.write(image_bytes)
        logger.info(f"File securely saved to {target_path}")
    except Exception as exc:
        logger.error(f"Failed to write image file to disk: {exc}")
        raise InvalidImageError("Internal server error saving file.")

    # Return path relative to static mount
    return f"/static/uploads/{unique_filename}"
