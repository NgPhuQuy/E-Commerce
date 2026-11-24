import os

DEFAULT_BASE_URL = "http://localhost:8080"
DEFAULT_TIMEOUT_SECONDS = 10.0


def get_base_url(cli_override: str | None = None) -> str:
    """Ưu tiên --base-url > biến môi trường BASE_URL > mặc định http://localhost:8080."""
    url = cli_override or os.getenv("BASE_URL") or DEFAULT_BASE_URL
    return url.rstrip("/")
