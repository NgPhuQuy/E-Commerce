import httpx

from support.models import Role, TestUser


def create_user(client: httpx.Client, role: Role = Role.CUSTOMER) -> TestUser:
    """Tạo user và lấy JWT token theo Role chỉ thông qua API (không ghi DB)."""
    raise NotImplementedError("Chưa hiện thực: chờ spec API Auth")
