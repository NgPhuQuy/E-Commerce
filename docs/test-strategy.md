# Test Strategy — EeasyShopping (Black-box API)

**Task:** 3.1 · **Phiên bản:** v0.2 · **Căn cứ:** D.1 (`docs/QUY_UOC_KY_THUAT.md`)

## 1. Phạm vi

- **Có:** kiểm thử hộp đen ở mức API, gọi qua **API Gateway** như một client thật (JWT, Role, mã lỗi, payload theo quy ước API).
- **Không:** unit test trong service, test giao diện, test tải/hiệu năng, truy vấn DB, import code của service.
- Muốn kiểm tra dữ liệu đã ghi thì **gọi API đọc lại**, không đọc DB.

## 2. Kỹ thuật thiết kế test case

| Kỹ thuật | Dùng khi |
|---|---|
| Phân lớp tương đương | Đầu vào chia được thành nhóm hợp lệ/không hợp lệ (email, UUID, Role) |
| Giá trị biên | Đầu vào có giới hạn số (ví dụ quantity 1..100: thử 0, 1, 100, 101) |
| Bảng quyết định | Kết quả phụ thuộc tổ hợp điều kiện (quyền × trạng thái × dữ liệu) |
| Chuyển trạng thái | Đối tượng có vòng đời (đơn hàng, SellerApplication, thanh toán) |
| Kịch bản use case | Luồng nghiệp vụ nhiều bước từ UC (ví dụ đăng ký → đăng nhập → thao tác) |

## 3. Mức ưu tiên

| Mức | Marker pytest | Ý nghĩa | Ví dụ |
|---|---|---|---|
| P1 | `@pytest.mark.p1` | Luồng chính, bảo mật, tiền; lỗi là chặn phát hành | Đăng nhập, phân quyền, checkout, thanh toán |
| P2 | `@pytest.mark.p2` | Luồng phụ và kiểm tra dữ liệu đầu vào quan trọng | Validate field, mã lỗi 400/404/409 |
| P3 | `@pytest.mark.p3` | Trường hợp hiếm, hiển thị, tiện ích | Định dạng thông báo, trường tùy chọn |

Chạy P1 trước (`uv run pytest -m p1`); P2, P3 chạy khi còn thời gian của sprint.

## 4. Quy tắc đặt tên test

- ID case: `<MODULE>-<CHỨC NĂNG>-<STT 2 số>`, ví dụ `AUTH-REG-03`. `MODULE` theo service: `AUTH`, `SHOP`, `CART`, `ORDER`, `PAYMENT`, `NOTI`, `AUDIT`.
- Tên hàm viết `snake_case` theo ID case: `test_<module>_<chức_năng>_<stt>` (ví dụ `test_auth_reg_03`), có thể thêm hậu tố mô tả ngắn; ghi ID case ở dòng đầu docstring. Một file `tests/test_<chức_năng>.py` cho mỗi nhóm chức năng.
- Test chưa làm đánh dấu `@pytest.mark.skip(reason="chưa làm")`.
- Gắn mức ưu tiên bằng `@pytest.mark.p1` / `p2` / `p3`; tận dụng `@pytest.mark.parametrize` cho giá trị biên và bảng quyết định.

## 5. Module `blackbox-tests/`

- Đặt tại thư mục gốc repo (`blackbox-tests/`), chỉ phụ thuộc **Python 3.12+ (`pytest` + `httpx`)**, quản lý bằng `uv` (`pyproject.toml`); **không** phụ thuộc code Java của bất kỳ service nào.
- Địa chỉ API Gateway truyền qua `--base-url` hoặc biến môi trường `BASE_URL` (mặc định `http://localhost:8080`).
- Dữ liệu test duy nhất mỗi lần chạy (`support/unique_data.py`) để các test không dính nhau.
- User/token theo Role được tạo **chỉ qua API** bằng `support/user_factory.py` và fixture `auth_client_factory` trong `tests/conftest.py`.
- Cách chạy:
  ```bash
  cd blackbox-tests
  uv run pytest                                  # chạy toàn bộ (mặc định http://localhost:8080)
  uv run pytest -m p1                            # chỉ chạy P1
  uv run pytest --base-url=http://localhost:8080 # chỉ định Gateway URL
  ```
