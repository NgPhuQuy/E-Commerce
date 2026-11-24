# Black-box API Tests — EeasyShopping

Module kiểm thử hộp đen ở mức API gọi qua **API Gateway** bằng **Python (`pytest` + `httpx`)**, tách biệt hoàn toàn với mã nguồn và DB của các service.

Xem đầy đủ chiến lược và quy ước tại [`docs/test-strategy.md`](../docs/test-strategy.md).

## Yêu cầu

- Python 3.12+ và [`uv`](https://docs.astral.sh/uv/) (được khuyến nghị).

## Cách chạy

```bash
cd blackbox-tests

# Cài dependency (lần đầu) và chạy toàn bộ test (mặc định http://localhost:8080)
uv run pytest

# Chỉ chạy nhóm ưu tiên P1
uv run pytest -m p1

# Trỏ sang địa chỉ Gateway khác
uv run pytest --base-url=http://localhost:8080
# hoặc dùng biến môi trường:
BASE_URL=http://localhost:8080 uv run pytest
```

## Cấu trúc

```text
blackbox-tests/
├── pyproject.toml          # Khai báo pytest + httpx và các marker p1/p2/p3
├── support/
│   ├── config.py           # Đọc BASE_URL (mặc định http://localhost:8080)
│   ├── models.py           # Role, TestUser
│   ├── unique_data.py      # Sinh email/UUID ngẫu nhiên tránh đụng dữ liệu
│   └── user_factory.py     # Tạo user/token theo Role chỉ qua API
└── tests/
    ├── conftest.py         # Fixture api_client, base_url, auth_client_factory
    └── test_sample.py      # Mẫu test case theo quy ước đặt tên
```
