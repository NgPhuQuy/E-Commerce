# Quy ước kỹ thuật — EeasyShopping

**Phiên bản:** v0.1 · **Ngày:** 19/10/2026

## 1. Kiến trúc

- Microservice gồm **6 service + API Gateway**. Sáu service: Auth, Shop, Cart, Order, Payment, Notification.
- **Audit** là thành phần dùng chung cho toàn hệ thống, không thuộc riêng service nào.
- **Last-Mile** là service riêng, đã có sẵn, chỉ tích hợp qua API. Gọi backend-to-backend, không dùng chung DB, không dùng chung JWT secret.
- **Ngoài phạm vi milestone này:** Review, Voucher, ShopFollow.

## 2. Dữ liệu

- Dùng 1 DB server. Mỗi service có schema/database riêng.
- Không join chéo giữa các service.

## 3. Giao tiếp

- Giữa các service dùng REST đồng bộ.

## 4. Cấu hình và log

- Cấu hình và secret đặt trong file `.env` (không commit lên git).
- Mỗi request có correlation-id để truy vết log xuyên service.

## 5. Quy ước API

| Hạng mục | Quy ước |
|---|---|
| Prefix | `/api` (chỉ dùng `/api/public/*` cho API mở công khai; còn lại mặc định phải qua xét quyền) |
| ID | UUID |
| Tiền | `DECIMAL(12,2)` trong DB, `BigDecimal` trong Java, đơn vị đồng. Không dùng `float`/`double` |
| Thời gian | UTC+7, định dạng ngày giờ mặc định của java |
| Xóa dữ liệu | Dùng soft-delete (không xóa cứng) |

## 6. Quy ước đặt tên (Java)

| Đối tượng | Quy ước | Ví dụ |
|---|---|---|
| Class | Viết hoa chữ đầu, mỗi từ sau viết hoa chữ đầu | `OrderItem` |
| Function / method | Viết thường chữ đầu, mỗi từ sau viết hoa chữ đầu | `createOrder` |
| Thuộc tính (field) | Viết thường chữ đầu, mỗi từ sau viết hoa chữ đầu | `shopId`, `createdAt` |
