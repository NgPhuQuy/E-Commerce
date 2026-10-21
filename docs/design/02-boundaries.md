# D.2 — Ranh giới service và dữ liệu mỗi service sở hữu

**Phiên bản:** v0.1 · **Ngày:** 21/10/2026

**Phụ thuộc:** D.1 (`docs/QUY_UOC_KY_THUAT.md` v0.1), RAS v2.0 (`docs/Requirements_Analysis&Specification.docx`)

---

## 1. Phạm vi và quy ước đọc

- Service trong phạm vi: **Auth, Shop, Cart, Order, Payment, Notification** + **API Gateway**. **Audit** là thành phần dùng chung (D.1 §1) và được coi như một service có DB riêng, chỉ nhận sự kiện.
- **Last-Mile** là hệ thống ngoài, chỉ tích hợp qua API (D.1 §1). Không vẽ vào ma trận service, chỉ nêu ở mục 6.
- **Ngoài phạm vi M1** (D.1 §1, ghi chú M1): Review, Voucher, ShopFollow. Các bảng liên quan chưa thuộc service nào trong tài liệu này.
- **API công khai** = đi qua Gateway, có JWT. **API nội bộ** = service gọi service, nằm dưới `/api/internal/**`, Gateway không route ra ngoài.
- **Sự kiện** = thông báo một chiều "việc đã xảy ra", bên phát không chờ kết quả. Cách vận chuyển (REST đẩy hay RabbitMQ) chưa chốt, xem Q1 ở mục 8. Danh sách bên dưới không đổi dù chọn cách nào.
- Tên bảng lấy từ ERD hiện có. Bảng RAS yêu cầu mà ERD chưa vẽ được đánh dấu *(mới)*.

---

## 2. Ma trận tổng hợp

| Service          | Sở hữu dữ liệu                                                                                                                                                                                        | API công khai (nhóm)                                                               | Gọi service nào (đồng bộ)                                | Phát sự kiện                                                                                      | Nhận sự kiện                                                                                                                                           |
|------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|----------------------------------------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Auth**         | user, role, permission, user_role, role_permission, address, refresh_session *(mới)*                                                                                                                  | register/login/logout/Google, hồ sơ, sổ địa chỉ, quản lý Role                      | —                                                        | `UserRegistered`, `PasswordResetRequested`, `UserRoleChanged`, `LoginFailed`, `UserStatusChanged` | —                                                                                                                                                      |
| **Shop**         | shop, seller_application, media_file, category, product_category, shop_category, product, product_image, sku, inventory, inventory_reservation, shop_collection *(mới)*, shop_collection_item *(mới)* | SellerApplication, Shop, Product/SKU/Inventory, Category, ShopCollection, tìm kiếm | **Auth** (cấp Role SELLER)                               | `SellerApplicationReviewed`, `ShopCreated`, `ShopStatusChanged`, `ProductModerated`               | —                                                                                                                                                      |
| **Cart**         | cart, cart_item                                                                                                                                                                                       | CRUD item trong giỏ                                                                | **Shop** (tra SKU: tồn tại, bán được, tên, giá hiện tại) | —                                                                                                 | `OrderPlaced` (dọn item đã mua)                                                                                                                        |
| **Order**        | order, shop_order, order_item, checkout_request *(mới)*                                                                                                                                               | checkout, xem/hủy đơn, SellerOrder của shop                                        | **Cart**, **Auth**, **Shop**, **Payment**                | `OrderPlaced`, `OrderCancelled`, `SellerOrderStatusChanged`                                       | `PaymentSucceeded`, `PaymentFailed`, `PaymentExpired`                                                                                                  |
| **Payment**      | payment, payment_attempt, provider_callback_log *(mới)*                                                                                                                                               | tạo thanh toán VNPay, trả về từ VNPay (return URL / IPN)                           | — (VNPay là hệ thống ngoài)                              | `PaymentSucceeded`, `PaymentFailed`, `PaymentExpired`                                             | —                                                                                                                                                      |
| **Notification** | notification, device_token *(mới)*, notification_delivery *(mới)*                                                                                                                                     | danh sách / đánh dấu đã đọc, đăng ký device token                                  | — (FCM, email là hệ thống ngoài)                         | —                                                                                                 | `UserRegistered`, `PasswordResetRequested`, `PaymentSucceeded/Failed`, `OrderPlaced`, `OrderCancelled`, `SellerOrderStatusChanged`                     |
| **Audit**        | audit_log *(mới)*                                                                                                                                                                                     | tra cứu audit (cần quyền `AUDIT_READ`)                                             | —                                                        | —                                                                                                 | tất cả sự kiện nhạy cảm: `UserRoleChanged`, `LoginFailed`, `UserStatusChanged`, `SellerApplicationReviewed`, `ProductModerated`, `OrderCancelled`, ... |
| **Gateway**      | (không có)                                                                                                                                                                                            | định tuyến, xác thực JWT, gắn correlation-id                                       | tất cả (chỉ chuyển tiếp)                                 | —                                                                                                 | —                                                                                                                                                      |

### Hướng gọi (đồ thị phải không có vòng đồng bộ)

```
Order ──► Cart
Order ──► Shop
Order ──► Auth
Order ──► Payment
Cart  ──► Shop
Shop  ──► Auth
Payment ┄(sự kiện)┄► Order     ← vòng chỉ tồn tại ở dạng sự kiện, không phải gọi đồng bộ
Order   ┄(sự kiện)┄► Cart
Mọi service ┄(sự kiện)┄► Audit / Notification
```

Gọi đồng bộ chỉ đi một chiều: **Order → Cart/Shop/Auth/Payment, Cart → Shop, Shop → Auth**. Chiều ngược lại đi bằng sự kiện (Payment → Order, Order → Cart). Nếu D.1 chọn sự kiện qua REST đẩy thì chiều ngược lại thành "callback có retry", xem Q1.

---

## 3. Chi tiết từng service

### 3.1 Auth

- **Sở hữu:** danh tính, Role/Permission, sổ địa chỉ giao hàng của Customer, phiên đăng nhập. Chỉ Auth ghi các bảng này.
- **API công khai:** `POST /api/auth/register|login|logout|google|refresh`; `GET|PUT /api/users/me`; `/api/users/me/addresses` (CRUD); quản lý Role-Permission cho Admin.
- **API nội bộ:**
    - `POST /api/internal/users/{userId}/roles`: thêm một Role cho user, **idempotent** (thêm lần 2 không lỗi, không trùng). Chỉ Shop được gọi.
    - `GET /api/internal/users/{userId}/addresses/{addressId}`: lấy một địa chỉ, có kiểm tra địa chỉ thuộc user. Chỉ Order gọi.
- **Gọi:** không gọi service nào.
- **Phát:** `UserRegistered` (kèm email để Notification gửi mail xác minh), `PasswordResetRequested`, `UserRoleChanged`, `LoginFailed`, `UserStatusChanged`.
- **Nhận:** không.
- **Token:** JWT mang `userId`, danh sách Role, danh sách Permission, `emailVerified`. Các service khác chỉ **xác minh chữ ký**, không gọi lại Auth ở mỗi request.

### 3.2 Shop

- **Sở hữu:** shop và mọi thứ gắn vào shop: hồ sơ đăng ký bán hàng, Product, SKU (giá), Inventory và Reservation, Category, ShopCollection. Giá và tồn kho nằm cùng DB với SKU.
- **API công khai:** `/api/seller-applications` (Customer gửi, Admin duyệt/từ chối); `/api/shops`; `/api/products`, `/api/skus`, inventory của shop mình; `/api/categories`; `/api/shops/{id}/collections`; tìm kiếm/duyệt public không cần đăng nhập.
- **API nội bộ:**
    - `POST /api/internal/skus:batch-get`: Cart tra nhiều SKU một lần (trạng thái, tên, giá hiện tại).
    - `POST /api/internal/inventory/reservations`: Order giữ hàng. Có `reservationId` làm khóa idempotent. **Phản hồi trả luôn snapshot xác nhận** (sku code, tên product, mô tả variant, đơn giá, shopId, tên shop) tại đúng thời điểm giữ hàng.
    - `POST /api/internal/inventory/reservations/{id}/commit` và `.../release`: Order xác nhận hoặc nhả hàng, đều idempotent.
- **Gọi:** Auth (`POST /api/internal/users/{userId}/roles`) khi Admin duyệt SellerApplication.
- **Phát:** `SellerApplicationReviewed`, `ShopCreated`, `ShopStatusChanged`, `ProductModerated`.
- **Nhận:** không.
- **Kiểm tra quyền:** Role SELLER, `emailVerified`, Permission đọc từ JWT. Việc "shop này có thuộc seller này không" Shop tự kiểm bằng dữ liệu của mình (`shop.owner_id`).

### 3.3 Cart

- **Sở hữu:** `cart` (owner = userId) và `cart_item` (sku_id, quantity). **Không lưu giá, tên, trạng thái bán.**
- **API công khai:** thêm / sửa số lượng / xóa / xem giỏ. Khi xem giỏ, Cart gọi Shop để lấy tên và giá hiện tại và trả về cho client dưới dạng "giá ước tính".
- **API nội bộ:** `GET /api/internal/carts/{userId}/items?ids=...`: Order lấy các item đã chọn khi checkout.
- **Gọi:** Shop (`skus:batch-get`) khi thêm item (kiểm SKU tồn tại, bán được) và khi xem giỏ.
- **Phát:** không.
- **Nhận:** `OrderPlaced` → xóa các item đã mua khỏi giỏ.
- **Khi Shop không trả lời:** vẫn trả danh sách item (sku_id, quantity) kèm cờ `priceUnavailable`, không tự điền giá cũ.

### 3.4 Order

- **Sở hữu:** đơn hàng tổng, đơn theo shop, dòng hàng và **snapshot thương mại** (tên, giá, địa chỉ giao, tên shop). Cả bảng `checkout_request` để retry không tạo đơn trùng.
- **API công khai:** `POST /api/orders/checkout` (có idempotency key), xem lịch sử đơn, hủy đơn theo trạng thái, Seller xem/xử lý SellerOrder của shop mình.
- **API nội bộ:** `POST /api/internal/orders/{orderId}/...` không cần mở cho service khác ở M1.
- **Gọi (điều phối checkout):** Cart (lấy item đã chọn) → Auth (lấy địa chỉ để snapshot) → Shop (giữ hàng, nhận snapshot giá) → tính tổng → Payment (tạo thanh toán với số tiền do Order tính). Khi thanh toán xong: Shop `commit`; khi thất bại/hết hạn/hủy: Shop `release`.
- **Phát:** `OrderPlaced`, `OrderCancelled`, `SellerOrderStatusChanged`.
- **Nhận:** `PaymentSucceeded`, `PaymentFailed`, `PaymentExpired`.
- **Không bao giờ:** đọc lại Product/SKU sau khi đã tạo đơn; tự trừ tồn kho.

### 3.5 Payment

- **Sở hữu:** giao dịch thanh toán, từng lần thử, nhật ký callback từ VNPay. Có lớp `PaymentGateway` (VNPay là bản cài đầu tiên) để thêm cổng khác không đổi phần còn lại (ghi chú M1: "mở rộng được nhiều cổng").
- **API công khai:** tạo yêu cầu thanh toán trả URL VNPay; return URL / IPN từ VNPay.
- **API nội bộ:** `POST /api/internal/payments`: Order tạo thanh toán (orderId, số tiền, idempotency key). Payment **không** nhận số tiền từ client.
- **Gọi:** không gọi service nào. Chỉ gọi VNPay.
- **Phát:** `PaymentSucceeded`, `PaymentFailed`, `PaymentExpired`.
- **Nhận:** không.
- **Không biết:** SKU, Product, tồn kho. Chỉ biết `orderId` và số tiền.

### 3.6 Notification

- **Sở hữu:** thông báo trong ứng dụng, device token (FCM), lịch sử gửi. Không phải nguồn trạng thái nghiệp vụ (RAS FR-NOTI-001).
- **API công khai:** xem danh sách, đánh dấu đã đọc, đăng ký/xóa device token.
- **Gọi:** không gọi service nào, chỉ gọi FCM/email.
- **Phát:** không.
- **Nhận:** các sự kiện giao dịch quan trọng ở bảng mục 2. Sự kiện mang đủ thông tin người nhận (userId, email nếu cần), nên Notification không phải hỏi lại Auth.
- Ngoài ghi chú M1 nhưng nằm trong 6 service của D.1, nên vẫn được vẽ ranh giới ở đây.

### 3.7 Audit

- **Sở hữu:** `audit_log` (chỉ thêm, không sửa, không xóa).
- **API công khai:** tra cứu, yêu cầu Permission `AUDIT_READ`.
- **Nhận:** sự kiện nhạy cảm từ các service khác (actor, action, target, time, result, correlation-id; không chứa mật khẩu, token, thông tin thanh toán).
- **Không có API ghi từ client**, và **không service nào ghi thẳng vào `audit_log`**. "Dùng chung" nghĩa là mọi service gửi sự kiện cho nó, **không** nghĩa là dùng chung thư viện ghi vào DB của nó.

### 3.8 API Gateway

Không sở hữu dữ liệu. Định tuyến theo prefix, xác minh JWT thô, gắn/chuyển `correlation-id`, chặn `/api/internal/**` từ bên ngoài. Không chứa logic nghiệp vụ.

---

## 4. Các điểm giao dễ sai (chốt)

| # | Điểm giao | Quy tắc chốt | Kiểm tra được bằng |
|---|---|---|---|
| 1 | **Order ↔ Product** | Order lưu snapshot (sku code, tên product, mô tả variant, đơn giá, tên shop, địa chỉ giao) lấy **một lần** từ phản hồi giữ hàng của Shop. Sau đó Order không bao giờ đọc lại Product. | Sửa tên/giá product xong, `GET order` cũ không đổi (RAS FR-ORD-003, BR-015, BR-031) |
| 2 | **Cart ↔ giá** | Cart chỉ lưu `sku_id` và `quantity`. Giá hiển thị lấy từ Shop khi xem. Giá chốt tính ở checkout. | Bảng `cart_item` không có cột giá/tên (RAS FR-CART-004, BR-009) |
| 3 | **Shop ↔ Role SELLER** | Shop không có bảng role, không ghi `user_role`. Duyệt xong Shop gọi Auth để thêm Role SELLER. | Xóa hết code Shop liên quan `user_role` mà luồng duyệt vẫn chạy, nhờ gọi Auth (RAS FR-SHOP-003, BR-039) |
| 4 | **Audit** | Audit chỉ nhận sự kiện. Không có API ghi, không service nào ghi vào DB của Audit. | `audit_log` có đúng 1 nơi ghi (consumer sự kiện trong Audit) |
| 5 | **Payment ↔ Order** | Số tiền do Order tính và gửi cho Payment. Kết quả thanh toán Payment báo bằng sự kiện. Payment không đọc bảng Order. | Payment không có `order_item`, không biết SKU |
| 6 | **Tồn kho** | Chỉ Shop trừ/giữ/nhả hàng. Order xin giữ/commit/release qua API có idempotency key. | Chỉ code Shop có câu lệnh UPDATE `inventory` (RAS FR-INV-003) |
| 7 | **Địa chỉ** | Địa chỉ Customer do Auth giữ. Order chụp snapshot lúc tạo đơn, không giữ FK. | Xóa/sửa địa chỉ không đổi đơn cũ (RAS BR-038) |

---

## 5. Nhật ký quyết định ranh giới (để phản biện)

Cột "Xem lại khi" là điều kiện cụ thể khiến quyết định nên được mở lại.

### B1. Giá, tồn kho và Inventory nằm trong Shop, không tách service thứ 7
- **Lý do:** SKU đổi giá/tồn kho cần cập nhật cùng một giao dịch DB; giữ hàng cần cập nhật có điều kiện nguyên tử trên cùng dữ liệu (RAS FR-INV-003). D.1 giới hạn **6 service**. ERD hiện đã vẽ inventory cạnh SKU.
- **Bị loại:** Inventory service riêng (đúng DDD hơn nhưng thêm 1 service, 1 DB, thêm 1 điểm lỗi cho nhóm 3 người).
- **Hệ quả:** Shop là service lớn nhất. Cần giữ code Inventory thành module riêng bên trong để tách sau không phải sửa service khác.
- **Xem lại khi:** tải đặt hàng cao hơn nhiều so với tải duyệt sản phẩm, cần scale riêng hai phần.

### B2. SellerApplication thuộc Shop (ERD hiện để trong Auth → phải sửa ERD)
- **Lý do:** Đây là luồng nghiệp vụ onboarding gắn với việc tạo shop (ghi chú M1 §2.2, RAS FR-SHOP-003). Auth chỉ cần biết kết quả: user có thêm Role SELLER hay không.
- **Bị loại:** để trong Auth như ERD hiện tại. Khi đó Auth phải biết thông tin shop (tên shop, CCCD, mã số thuế), vi phạm "đổi trong Shop không sửa Auth".
- **Hệ quả:** chuyển `seller_application` và `media_file` sang schema Shop. CCCD/MST là dữ liệu nhạy cảm, Shop phải mã hóa hoặc che khi trả về.
- **Xem lại khi:** quy trình duyệt cần dữ liệu danh tính mà Auth đã giữ (ví dụ xác minh KYC chung cho mọi vai trò).

### B3. Cấp Role SELLER bằng cách Shop gọi Auth (đồng bộ, idempotent)
- **Lý do:** Chỉ Auth ghi `user_role`. Gọi đồng bộ vì Shop cần biết kết quả trước khi chuyển application sang APPROVED (RAS: "SELLER role chỉ được gán sau khi approve").
- **Thứ tự:** gọi Auth trước, thành công mới đặt APPROVED. Nếu Auth lỗi, application vẫn UNDER_REVIEW, Admin bấm lại an toàn vì API idempotent.
- **Bị loại:** Shop phát sự kiện, Auth nghe và tự cấp. Mất xác nhận: Admin thấy APPROVED mà user chưa có quyền.
- **Hệ quả:** Shop phụ thuộc Auth lúc runtime (chỉ ở luồng duyệt, không ảnh hưởng đọc Product).
- **Xem lại khi:** có nhiều loại phê duyệt khác cũng cần cấp quyền, lúc đó cân nhắc luồng chung.

### B4. Order điều phối checkout, Cart chỉ là nguồn đọc
- **Lý do:** Order là nơi chịu trách nhiệm cuối về tiền và đơn (RAS BR-010, FR-CHK-001: fail-all, bù trừ). Một nơi điều phối thì dễ test và dễ thấy chỗ bù trừ.
- **Bị loại:** Cart tự gọi Shop/Payment rồi tạo đơn. Cart sẽ biết quá nhiều.
- **Hệ quả:** Order có 4 phụ thuộc đồng bộ (Cart, Auth, Shop, Payment). Là điểm lỗi tập trung. Cần timeout và bù trừ (release) rõ ràng.
- **Xem lại khi:** số bước checkout tăng (voucher, ship quote Last-Mile) làm Order quá phức tạp, lúc đó tách bước điều phối riêng.

### B5. Snapshot giá lấy từ phản hồi giữ hàng, không gọi Shop hai lần
- **Lý do:** Nếu đọc giá một lần rồi giữ hàng lần nữa, giá có thể đổi giữa hai lần và snapshot lệch với hàng đã giữ. Gộp một lần thì snapshot đúng với thứ đã giữ.
- **Bị loại:** Order gọi `GET sku` rồi `POST reserve`.
- **Hệ quả:** API `reservations` của Shop phải trả nhiều trường hơn, và đó là hợp đồng Order phụ thuộc vào.
- **Xem lại khi:** cần hiển thị giá trước khi giữ hàng cho cùng một bước xác nhận.

### B6. Cart không lưu giá, kể cả giá cache
- **Lý do:** RAS cho phép "cache display snapshot", nhưng cache giá trong Cart tạo hai nguồn giá và dễ bị nhầm là giá thanh toán.
- **Bị loại:** lưu `price_at_add` để hiện nhanh.
- **Hệ quả:** mỗi lần xem giỏ phải gọi Shop (một lệnh batch). Shop chậm thì giỏ chậm. Giảm nhẹ bằng cờ `priceUnavailable`.
- **Xem lại khi:** đo được độ trễ xem giỏ vượt ngưỡng chấp nhận.

### B7. Category thuộc Shop
- **Lý do:** `product_category` nối Product với Category. Tách Category ra service khác sẽ buộc join chéo DB.
- **Bị loại:** Category ở Auth hoặc service riêng.
- **Hệ quả:** Admin quản lý Category qua API của Shop với Permission riêng.
- **Xem lại khi:** nhiều service khác cũng cần dùng Category.

### B8. Audit là service nhận sự kiện, DB riêng
- **Lý do:** D.1 nói Audit dùng chung, không thuộc service nào. Nếu là thư viện ghi thẳng vào DB, mọi service phải biết schema Audit và thành "nhiều bên cùng ghi một bảng".
- **Bị loại:** thư viện chung ghi vào bảng ở DB mỗi service; Audit gọi ngược các service để hỏi.
- **Hệ quả:** nếu sự kiện mất thì thiếu log. Cần cơ chế gửi lại, và với D.1 REST-only, Audit không đảm bảo nhận đủ khi đang tắt, xem Q1.
- **Xem lại khi:** yêu cầu pháp lý đòi log không được mất.

### B9. Địa chỉ Customer ở Auth; địa chỉ shop ở Shop
- **Lý do:** Địa chỉ Customer gắn với User (ERD hiện để trong Auth). Địa chỉ shop (trụ sở, ghi chú M1: 1 địa chỉ/shop) là thuộc tính của shop.
- **Hệ quả:** hai khái niệm "address" ở hai service, cùng tên bảng nhưng khác schema.
- **Xem lại khi:** shop cần nhiều địa chỉ lấy hàng cho Last-Mile (ghi chú họp nói 1 shop nhiều địa chỉ, M1 chỉ làm 1).

### B10. Thông tin nhận thông báo đi kèm trong sự kiện
- **Lý do:** nếu Notification phải gọi Auth để lấy email/token, nó thành phụ thuộc đồng bộ vào Auth, và Auth chết thì thông báo chết (trái RAS FR-NOTI-002: không chặn transaction chính).
- **Hệ quả:** sự kiện chứa email/userId. Cần che dữ liệu nhạy cảm trong log.
- **Xem lại khi:** sự kiện mang quá nhiều dữ liệu cá nhân gây rủi ro lộ.

### B11. JWT ký bất đối xứng, các service chỉ xác minh
- **Lý do:** D.1 chỉ nói Last-Mile không dùng chung JWT secret. Với RS256, chỉ Auth giữ khóa ký, service khác chỉ cần khóa công khai. Không phải chia sẻ secret giữa nhiều service.
- **Bị loại:** secret HS256 chia cho cả 6 service. Một service lộ secret thì ai cũng giả được token.
- **Hệ quả:** khóa công khai cần phân phối và xoay vòng.
- **Xem lại khi:** nhóm thấy việc xoay khóa quá nặng ở giai đoạn đầu. Đây là đề xuất cần D.1 xác nhận (Q3).

---

## 6. Last-Mile (ngoài M1, ghi để không vẽ sai sau này)

- Do **Order** gọi (Order sở hữu SellerOrder, RAS BR-044), không phải Shop.
- Không dùng chung DB, không dùng chung JWT secret (D.1).
- Lỗi Last-Mile không làm hỏng đọc đơn (RAS BR-027). Order lưu mã vận đơn tham chiếu, không lưu trạng thái GPS.
- Phí ship quote theo SellerOrder, snapshot vào Order.

---

## 7. Thử ranh giới

### 7.1 Không 2 service cùng ghi 1 bảng

| Bảng | Service duy nhất được ghi | Service khác chỉ làm gì |
|---|---|---|
| user, role, permission, user_role, role_permission, address, refresh_session | Auth | Shop gọi API Auth để **yêu cầu** thêm role, không ghi |
| shop, seller_application, media_file, category, product*, sku, inventory, inventory_reservation, shop_collection* | Shop | Order/Cart gọi API Shop |
| cart, cart_item | Cart | Order đọc qua API Cart, dọn giỏ do Cart tự làm khi nhận `OrderPlaced` |
| order, shop_order, order_item, checkout_request | Order | Payment chỉ báo bằng sự kiện |
| payment, payment_attempt, provider_callback_log | Payment | Order xin tạo qua API |
| notification, device_token, notification_delivery | Notification | — |
| audit_log | Audit | Mọi service chỉ gửi sự kiện |

**Kết quả:** mỗi bảng đúng 1 service ghi. Hai chỗ dễ vi phạm nhất đã xử lý: `user_role` (B3), `inventory` (B1, chỉ Shop trừ).

### 7.2 Không join DB chéo service

Mọi tham chiếu qua ranh giới là **UUID thường, không FOREIGN KEY, không JOIN**:

| Cột | Ở service | Trỏ tới (service khác) |
|---|---|---|
| `shop.owner_id` | Shop | user (Auth) |
| `cart.owner`, `cart_item.sku_id` | Cart | user (Auth), sku (Shop) |
| `order.user_id` | Order | user (Auth) |
| `shop_order.shop_id`, `order_item.sku_id` | Order | shop, sku (Shop) |
| `payment.order_id` | Payment | order (Order) |
| `notification.user_id` | Notification | user (Auth) |
| `audit_log.actor_id`, `target_id` | Audit | tùy sự kiện |

Màn hình cần dữ liệu hai nơi (ví dụ xem giỏ có tên và giá) thì **service sở hữu giao diện đó gọi API** (Cart gọi Shop), không join.

### 7.3 Đổi bên trong một service thì service khác không phải sửa

| Thay đổi | Service đổi | Service khác phải sửa? | Vì sao |
|---|---|---|---|
| Đổi cột `product.detail`, thêm cột mới | Shop | Không | Chỉ lộ qua API; Order dùng snapshot |
| Thay thuật toán giữ hàng (khóa bi quan thay vì cập nhật có điều kiện) | Shop | Không | Order chỉ thấy API `reservations` |
| Đổi cấu trúc role-permission (thêm bảng trung gian) | Auth | Không | Service khác chỉ đọc claim trong JWT |
| Thêm cổng thanh toán MoMo | Payment | Không | Nằm sau `PaymentGateway`; Order chỉ gọi `POST /payments` |
| Đổi DB Notification sang MongoDB | Notification | Không | Không ai đọc DB của nó |
| Đổi tên product sau khi đã mua | Shop | Không | Order giữ snapshot |
| **Đổi hình dạng phản hồi `reservations`** | Shop | **Có: Order** | Đây là hợp đồng công khai giữa hai service, phải đổi cùng phiên bản |
| **Đổi tên/ý nghĩa sự kiện `PaymentSucceeded`** | Payment | **Có: Order, Notification** | Sự kiện là hợp đồng, đổi thì bên nhận phải đổi |

Hai dòng cuối cố ý nêu ra: hợp đồng API/sự kiện là chỗ **được phép** gây lan truyền, nên cần đánh phiên bản (D.3 nếu có) và không đổi tùy tiện.

---

## 8. Câu hỏi mở và sai lệch cần xử lý

### Cần D.1 trả lời

- **Q1 — REST hay sự kiện?** D.1 §3 ghi "giữa các service dùng REST đồng bộ", nhưng yêu cầu D.2 và RAS cần sự kiện (Audit chỉ nhận sự kiện, Notification không chặn giao dịch), và TECHSTACK ghi RabbitMQ ở trạng thái READY. Đề xuất: giữ khái niệm "sự kiện" như mục 2; M1 vận chuyển bằng REST đẩy một chiều (POST tới `/api/internal/events`, có retry); chuyển sang RabbitMQ sau mà **không đổi ma trận**. Rủi ro của REST đẩy: bên nhận đang tắt thì mất sự kiện nếu không có hàng đợi gửi lại ở bên phát (outbox).
- **Q2 — Cách vận chuyển sự kiện Payment → Order** phụ thuộc Q1. Nếu REST đẩy, đó là callback có retry và tạo vòng phụ thuộc lúc chạy giữa Order và Payment.
- **Q3 — Chuẩn JWT:** D.1 chưa ghi thuật toán ký. Đề xuất RS256 (B11).
- **Q4 — "6 service + Gateway" có coi Audit là service thứ 7 không?** D.1 §1 nói Audit "dùng chung, không thuộc service nào". Tài liệu này coi nó là deployable riêng, vì đó là cách duy nhất để "chỉ nhận sự kiện".

### Sai lệch giữa ERD hiện tại và ranh giới trong tài liệu này (cần sửa ERD, không phải sửa ranh giới)

1. `seller_application`, `media_file` đang ở ERD Auth → chuyển sang Shop (B2).
2. `cart_item.product_id` → đổi thành `sku_id` (RAS FR-CART-001, BR-006: SKU là đơn vị bán).
3. `order_item` chỉ có `SKU` (mã) và `price` → thiếu snapshot tên product, mô tả variant, discount; `shop_order` thiếu `shop_name`; `order` có `address` nhưng chưa tách phí ship/giảm giá (BR-066, M1 có thể bỏ voucher nhưng nên chừa chỗ).
4. `inventory_reservation` thiếu `status` (ACTIVE/COMMITTED/RELEASED/EXPIRED) và `expires_at` (RAS FR-INV-003: hết hạn 15 phút).
5. `payment` thiếu mã tham chiếu VNPay (`provider_ref`, unique, RAS BR-021).
6. Chưa có ERD cho Audit, và ERD Notification mới có `content`.

### Phạm vi M1 và các mục không phải "service"

- **Hạ tầng (Docker, Docker Compose)** và **Kiểm thử BlackBox** không thuộc service nào. Hạ tầng thuộc repo/ops; mỗi service tự giữ bộ test của mình.
- **Receipt/biên nhận** (RAS FR-PAY-006) chưa nằm trong M1. Nếu làm, đề xuất thuộc Order vì dùng dữ liệu snapshot, lấy số tham chiếu từ Payment qua API.
- **"CRUD hóa đơn"** trong M1 được hiểu là CRUD Order/SellerOrder/OrderItem (Order). Nếu ý là Receipt thì xem mục trên.

---

## 9. Mỗi chức năng M1 thuộc đúng 1 service

| #  | Chức năng (ghi chú M1)                       | Service duy nhất        | Ghi chú                                                     |
|----|----------------------------------------------|-------------------------|-------------------------------------------------------------|
| 1  | Đóng gói backend bằng Docker                 | — (hạ tầng)             | Mỗi service có Dockerfile theo `docker/Dockerfile.template` |
| 2  | Chạy hệ thống bằng Docker Compose            | — (hạ tầng)             |                                                             |
| 3  | Đăng ký (`register`)                         | **Auth**                |                                                             |
| 4  | Đăng nhập, đăng xuất                         | **Auth**                |                                                             |
| 5  | Đăng nhập Google                             | **Auth**                |                                                             |
| 6  | Phân quyền 3 Role, mỗi Role nhiều Permission | **Auth**                | CUSTOMER, SELLER, ADMIN                                     |
| 7  | `SellerApplication`                          | **Shop**                | Cấp Role gọi Auth (B2, B3)                                  |
| 8  | Tạo shop (1 địa chỉ trụ sở)                  | **Shop**                |                                                             |
| 9  | CRUD `Product`                               | **Shop**                | Kèm SKU và Inventory (B1)                                   |
| 10 | Quản lý `ShopCollection`                     | **Shop**                |                                                             |
| 11 | Tích hợp VNPay                               | **Payment**             |                                                             |
| 12 | Mở rộng nhiều cổng thanh toán                | **Payment**             | `PaymentGateway`                                            |
| 13 | CRUD hóa đơn                                 | **Order**               |                                                             |
| 14 | CRUD `CartItem` trong `Cart`                 | **Cart**                |                                                             |
| 15 | Ghi log giao tác nhạy cảm                    | **Audit**               | Chỉ nhận sự kiện                                            |
| 16 | BlackBox Test (JUnit)                        | — (mỗi service tự test) |                                                             |

**Kiểm tra "xong khi":** 13 chức năng nghiệp vụ (dòng 3 đến 15) đều thuộc đúng 1 service; hai dòng hạ tầng và một dòng kiểm thử không phải chức năng của service nghiệp vụ nên ghi rõ "—". Notification không có dòng trong M1 nhưng vẫn có ranh giới ở mục 3.6.
