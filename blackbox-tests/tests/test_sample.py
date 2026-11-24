import httpx
import pytest

from support.unique_data import random_email


@pytest.mark.p1
def test_sample_setup_01(api_client: httpx.Client, base_url: str) -> None:
    """SAMPLE-SETUP-01 — Test mẫu kiểm tra khung black-box test chạy được bằng uv run pytest."""
    assert str(api_client.base_url).rstrip("/") == base_url
    assert random_email() != random_email()


@pytest.mark.p1
@pytest.mark.skip(reason="chưa làm")
def test_auth_reg_03(api_client: httpx.Client) -> None:
    """AUTH-REG-03 — Mẫu test case chưa hiện thực.

    Khi triển khai: chỉ gọi API qua api_client (API Gateway), không truy vấn DB.
    """
    raise NotImplementedError
