"""
Storage Service for AURA-Rx Backend
Guarantees original prescription image preservation and traceability as mandated by PLAN.md Section 5.2.
Never overwrites, destructively crops, or discards the original uploaded prescription file.
"""

import re
import uuid
from pathlib import Path
from typing import Tuple, Optional
from ..config import get_settings
from ..schemas.error import ErrorCode


class FileValidationError(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class StorageService:
    def __init__(self):
        self.settings = get_settings()
        self.upload_dir = self.settings.ensure_upload_dir_exists()

    def validate_file_metadata(self, filename: str, content_type: Optional[str], size: int) -> None:
        """
        Validates content type and file size against security and diagnostic policies.
        """
        # Validate file size
        if size > self.settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = self.settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
            raise FileValidationError(
                code=ErrorCode.FILE_TOO_LARGE,
                message=f"Uploaded file size ({size / (1024 * 1024):.1f} MB) exceeds maximum allowed threshold of {max_mb:.0f} MB.",
                status_code=413,
            )

        # Validate content type / extension
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".svg"}
        ext = Path(filename).suffix.lower() if filename else ""

        if content_type and content_type.lower() not in self.settings.ALLOWED_IMAGE_TYPES and ext not in valid_extensions:
            allowed_list = ", ".join(self.settings.ALLOWED_IMAGE_TYPES)
            raise FileValidationError(
                code=ErrorCode.INVALID_FILE_TYPE,
                message=f"File format '{content_type or ext}' is not supported for prescription ingestion. Allowed MIME types: {allowed_list}.",
                status_code=415,
            )

    def save_prescription_image(self, file_bytes: bytes, original_filename: str) -> Tuple[Path, str]:
        """
        Saves uploaded prescription bytes with an immutable, cryptographically safe filename.
        Returns:
            (saved_path, public_url)
        """
        clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", original_filename or "prescription.png")
        ext = Path(clean_name).suffix or ".png"
        unique_id = uuid.uuid4().hex[:12]
        saved_filename = f"rx_{unique_id}_{Path(clean_name).stem}{ext}"
        saved_path = self.upload_dir / saved_filename

        with open(saved_path, "wb") as f:
            f.write(file_bytes)

        # Publicly accessible URL served via FastAPI static files mount
        public_url = f"/uploads/{saved_filename}"
        return saved_path, public_url

    def get_prescription_image_path(self, filename: str) -> Optional[Path]:
        """Safely locates a prescription image by filename, preventing directory traversal."""
        safe_name = Path(filename).name
        target = self.upload_dir / safe_name
        if target.is_file():
            return target
        return None
