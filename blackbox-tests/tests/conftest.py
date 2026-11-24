from collections.abc import Callable, Generator

import httpx
import pytest

from support.config import DEFAULT_TIMEOUT_SECONDS, get_base_url
from support.models import Role, TestUser
from support.user_factory import create_user


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="Địa chỉ API Gateway (mặc định: biến môi trường BASE_URL hoặc http://localhost:8080)",
    )


@pytest.fixture(scope="session")
def base_url(request: pytest.FixtureRequest) -> str:
    return get_base_url(request.config.getoption("--base-url"))


@pytest.fixture()
def api_client(base_url: str) -> Generator[httpx.Client, None, None]:
    """HTTP client chưa gắn token — dùng cho /api/public/* hoặc test 401."""
    with httpx.Client(base_url=base_url, timeout=DEFAULT_TIMEOUT_SECONDS) as client:
        yield client


@pytest.fixture()
def auth_client_factory(
    base_url: str,
    api_client: httpx.Client,
) -> Generator[Callable[[Role], tuple[httpx.Client, TestUser]], None, None]:
    """Tạo nhanh HTTP client đã gắn sẵn Bearer token theo Role và tự đóng sau test."""
    created_clients: list[httpx.Client] = []

    def _make(role: Role = Role.CUSTOMER) -> tuple[httpx.Client, TestUser]:
        user = create_user(api_client, role=role)
        client = httpx.Client(
            base_url=base_url,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            headers={"Authorization": f"Bearer {user.token}"},
        )
        created_clients.append(client)
        return client, user

    yield _make

    for client in created_clients:
        client.close()
