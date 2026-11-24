import uuid


def random_email(prefix: str = "bbt") -> str:
    """Sinh email duy nhất cho mỗi lần chạy để các test không dính nhau."""
    return f"{prefix}-{uuid.uuid4()}@example.test"


def random_uuid() -> str:
    return str(uuid.uuid4())
