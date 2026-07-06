import re
from typing import Optional, Tuple


def validate_slug(value: str) -> Tuple[bool, Optional[str]]:
    """Validate and normalize a URL slug. Returns (is_valid, normalized_slug)."""
    if not value or not value.strip():
        return False, None
    slug = value.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")
    if not slug:
        return False, None
    return True, slug


def validate_required(value: str, field_name: str, max_length: int = 500) -> Tuple[bool, Optional[str]]:
    """Validate a required string field. Returns (is_valid, error_message)."""
    if not value or not value.strip():
        return False, f"{field_name} is required."
    if len(value.strip()) > max_length:
        return False, f"{field_name} must be {max_length} characters or fewer."
    return True, None


def validate_email(value: str) -> Tuple[bool, Optional[str]]:
    """Basic email format validation."""
    if not value or not value.strip():
        return True, None  # email is optional on most forms
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, value.strip()):
        return False, "Invalid email format."
    return True, None


def validate_url(value: str) -> Tuple[bool, Optional[str]]:
    """Validate URL format (optional field)."""
    if not value or not value.strip():
        return True, None
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    if not re.match(pattern, value.strip()):
        return False, "Invalid URL format. Must start with http:// or https://"
    return True, None


def validate_int(value, field_name: str, min_val: int = 0) -> Tuple[bool, Optional[str]]:
    """Validate an integer within a range."""
    try:
        v = int(value)
        if v < min_val:
            return False, f"{field_name} must be at least {min_val}."
        return True, None
    except (TypeError, ValueError):
        return False, f"{field_name} must be a valid integer."
