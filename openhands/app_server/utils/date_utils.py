from datetime import UTC, datetime


def utc_now():
    """Return the current time in UTC format (Since datetime.utcnow is deprecated)"""
    return datetime.now(UTC)
