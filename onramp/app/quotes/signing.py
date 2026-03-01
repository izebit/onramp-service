"""Generic signing."""

import hashlib
from datetime import datetime, timezone


def get_signature(*, algorithm: str = "sha256", **parts: object) -> str:
    """Build canonical payload from named parts (sorted by name) and return hex digest."""
    if algorithm != "sha256":
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    payload = "".join(str(parts[k]) for k in sorted(parts))
    return hashlib.sha256(payload.encode()).hexdigest()


def verify_signature(signature: str, *, now: datetime | None = None, **parts: object) -> bool:
    """Check that the signature matches the recomputed one and that the timestamp is not expired.

    Uses the same canonical payload as get_signature (parts sorted by name).
    If ``expired_at`` is in parts, it must be an ISO-format datetime string; validity is
    checked as ``now < expired_at`` (default ``now`` is UTC).
    """
    expected = get_signature(**parts)
    if signature != expected:
        return False
    if "expired_at" in parts:
        expired = datetime.fromisoformat(str(parts["expired_at"]))
        if now is None:
            now = datetime.now(timezone.utc)
        if now >= expired:
            return False
    return True
