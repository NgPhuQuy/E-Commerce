# EeasyShopping – Cart Service API Contract (Milestone 1)

**Task:** SCRUM-191 / D.8  
**Phiên bản:** v1.1 (rà soát cuối 30/10/2026)  
**Trạng thái:** **APPROVED – baseline thiết kế do Cart Service sở hữu, chờ team review/merge**. Các interface phụ thuộc Shop/Order và cơ chế truyền OrderPlaced ở Mục 4 là **đề xuất tích hợp, chưa được phê duyệt liên service**. Không được hiểu Approved là các bên liên quan đã ký duyệt.  
**Phạm vi:** Cart Service, API công khai và điểm giao tiếp nội bộ liên quan Cart

## 1. Căn cứ và phạm vi

- `docs/QUY_UOC_KY_THUAT.md` (D.1): kiến trúc microservice, `/api`, UUID, quyền và quy ước dữ liệu.
- `docs/design/02-boundaries.md` (D.2): Cart sở hữu `cart`, `cart_item`; không sở hữu SKU/giá/tồn kho; gọi Shop để lấy thông tin hiện tại; Order điều phối checkout.
- `docs/design/Milestone_1/EeasyShopping_M1_Use_Case_Specifications.docx` (D.3): `UC-CART-001`, `UC-CHK-001`.
- `docs/design/Milestone_1/EeasyShopping_M1_Permission_Matrix.docx`: `CART_READ_SELF`, `CART_MANAGE_SELF`.
- `docs/Requirements_Analysis&Specification.docx`: `FR-CART-001..004`.
- `docs/design/08-cart/business-rules.md`: các quyết định D.8-01..D.8-10.
- `docs/design/08-cart/cart.dbml`: mô hình dữ liệu Cart, `version`, soft-delete và xử lý lặp `OrderPlaced`.

**Đã chốt trong task:** API-01 (5 REST endpoint); API-02 (GET vẫn `200` với dữ liệu giỏ khi Shop lỗi); API-03 (`availabilityStatus` ba trạng thái, bỏ `available`). Bản v1.1 xác định thêm trong phạm vi thiết kế Cart: PATCH sử dụng `expectedVersion`; trả `version` cho CartItem; các quy tắc lỗi, chuyển trạng thái, và kiểm tra concurrency như tài liệu này.

**Phạm vi phê duyệt:** Đây là hợp đồng triển khai **của Cart**, không phải quyết định thay Shop/Order hoặc ADR chung. Bất kỳ endpoint nội bộ/payload nào mang nhãn **đề xuất tích hợp** chỉ được coi là phụ thuộc cần xác nhận. Thay đổi contract liên service phải cập nhật phiên bản và review lại trước khi tích hợp.

**Nguyên tắc:** Cart lưu `skuId`, `quantity` và metadata; không lưu giá authoritative hay trạng thái bán của SKU. Shop là nguồn thông tin SKU/giá; Order kiểm tra lại giá/tồn kho và điều phối checkout. Không join DB hoặc tạo FK xuyên service.

## 2. Quy ước chung

### 2.1. Đường dẫn và xác thực

- Public Cart API qua Gateway: `/api/cart` và `/api/cart/items...` (đây là đường dẫn đã chọn ở API-01, **chưa mặc định thêm `/v1`**).
- JWT hợp lệ và quyền `CUSTOMER` tương ứng theo Permission Matrix M1.
- `GET /api/cart`: `CART_READ_SELF`.
- Các thao tác `POST`, `PATCH`, `DELETE`: `CART_MANAGE_SELF`.
- Backend lấy `userId` từ danh tính đã xác thực; **không nhận `userId` hoặc `ownerId` từ client** để xác định chủ giỏ.
- Các đường `/api/internal/**` **không được public qua Gateway**. Bắt buộc xác thực service-to-service và kiểm tra quyền gọi nội bộ. Phương thức xác thực service cụ thể cần khớp ADR chung.
- ID sử dụng UUID. Tiền sử dụng `BigDecimal`/`DECIMAL(12,2)` khi có xử lý trong Java/DB; JSON giá là số thập phân tính theo VND, không dùng số dấu phẩy động để tính tiền.
- Request mang/được gán `correlation-id` để truy vết theo quy ước chung.

### 2.2. `CartResponse`

```json
{
  "cartId": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {
      "itemId": "a91b46e2-8ef2-4ac1-9d15-3bd3c7c9a201",
      "skuId": "23e4567e-e89b-42d3-a456-426614174000",
      "quantity": 2,
      "version": 4,
      "availabilityStatus": "AVAILABLE",
      "priceUnavailable": false,
      "estimatedUnitPrice": 150000.0
    }
  ]
}
```

| Field                | Kiểu                | Ý nghĩa                                                                                      |
| -------------------- | ------------------- | -------------------------------------------------------------------------------------------- |
| `cartId`             | UUID hoặc `null`    | `null` nếu Cart chưa được tạo (lazy creation)                                                |
| `items`              | array               | Chỉ gồm CartItem chưa soft-delete                                                            |
| `itemId`             | UUID                | Định danh CartItem                                                                           |
| `skuId`              | UUID                | Tham chiếu SKU do Shop quản lý                                                               |
| `quantity`           | integer             | Từ 1 đến 100                                                                                 |
| `version`            | integer (64-bit)    | Phiên bản CartItem phục vụ cập nhật có điều kiện; tăng sau mỗi thay đổi quantity/soft-delete |
| `availabilityStatus` | enum                | `AVAILABLE`, `UNAVAILABLE`, `UNKNOWN`                                                        |
| `priceUnavailable`   | boolean             | `true` khi không lấy được giá hiện tại                                                       |
| `estimatedUnitPrice` | decimal hoặc `null` | Giá một đơn vị lấy từ Shop, **chỉ tham khảo**                                                |

**Quy tắc trạng thái:**

- `AVAILABLE`: Shop xác nhận SKU sellable tại lúc truy vấn; không phải bảo đảm còn hàng lúc checkout.
- `UNAVAILABLE`: Shop xác nhận SKU không sellable (ngừng bán/không đủ điều kiện bán). Giữ item và không cho checkout item đó.
- `UNKNOWN`: chưa xác minh được trạng thái Shop, ví dụ timeout. Không tự hiểu là SKU ngừng bán; không dùng kết quả này để cho checkout thành công.
- Nếu Shop không phản hồi cho một SKU: `availabilityStatus="UNKNOWN"`, `priceUnavailable=true`, `estimatedUnitPrice=null`.
- Nếu Shop xác minh SKU không bán được nhưng vẫn trả giá hợp lệ, giá có thể hiển thị dưới dạng tham khảo. Nếu không có giá hiện tại, trả `null` và `priceUnavailable=true`; **không tự dựng giá cũ**.
- Không lưu các field tính từ Shop trong bảng `cart_item`.

### 2.3. Response lỗi chuẩn trong phạm vi Cart (phải đối chiếu chuẩn chung khi tích hợp)

```json
{
  "code": "CART_QUANTITY_INVALID",
  "message": "Số lượng phải là số nguyên từ 1 đến 100.",
  "correlationId": "2c3d2abc-2a54-4e62-8f5e-d11baf5a3021"
}
```

`code` là mã nghiệp vụ ổn định trong Cart; `message` phục vụ client. **Shape lỗi này là baseline thiết kế Cart v1.1**, nhưng chưa thay thế Error Contract dùng chung nếu nhóm ban hành một chuẩn khác. Khi tích hợp phải dùng adapter/điều chỉnh contract được review, không âm thầm làm sai các service khác. Không trả stack trace, dữ liệu giỏ người khác hoặc thông tin nội bộ Shop.

## 3. API công khai

### 3.1. `GET /api/cart`

**Permission:** `CART_READ_SELF`  
**Request body:** Không có  
**Thành công:** `200 OK`, trả `CartResponse`.

**Giỏ chưa tồn tại:**

```json
{ "cartId": null, "items": [] }
```

GET không tự ghi database. Nếu Shop timeout/toàn bộ hoặc từng phần, vẫn trả `200` và đầy đủ CartItem đã lưu; những SKU chưa xác minh được có `UNKNOWN`, `priceUnavailable=true`, `estimatedUnitPrice=null`. Điều kiện: Cart DB còn truy xuất được. Nếu Cart DB lỗi, không được trả giỏ rỗng giả.

**Lỗi:** `401` chưa xác thực, `403` không có permission, `500` khi Cart DB lỗi (hoặc `503` nếu team quy định lỗi DB tạm thời là Service Unavailable; cần thống nhất trước tích hợp).

### 3.2. `POST /api/cart/items`

**Permission:** `CART_MANAGE_SELF`  
**Request:**

```json
{
  "skuId": "23e4567e-e89b-42d3-a456-426614174000",
  "quantity": 3
}
```

**Thành công (API-01):** `200 OK`, trả `CartResponse` phản ánh dữ liệu đã commit. Trả `200` kể cả khi tạo Cart lần đầu theo contract D.8.

**Quy tắc:**

1. Kiểm tra JWT/permission/ownership từ server; `skuId` là UUID hợp lệ, `quantity` nguyên trong `[1,100]`.
2. Xác minh SKU tồn tại và sellable thông qua Shop. Nếu Shop không thể xác minh, **từ chối ghi**.
3. Nếu Cart chưa tồn tại, tạo Cart và item trong cùng transaction (lazy creation).
4. Nếu SKU đã tồn tại trong Cart thì cộng dồn quantity. Tổng sau cộng không vượt 100; vượt giới hạn thì không thay đổi Cart.
5. **Chiến lược concurrency bắt buộc:** Sau khi Shop xác minh SKU, bắt đầu transaction Cart DB. Khóa dòng `cart` của owner (`SELECT ... FOR UPDATE`) trước khi tìm/thêm/sửa CartItem. Nếu Cart chưa tồn tại, `INSERT cart` dựa vào UNIQUE `owner_id`; khi bị duplicate key do request khác vừa tạo Cart, rollback và retry toàn bộ transaction theo giới hạn cấu hình, sau đó khóa dòng Cart mới. Với item active đã tồn tại, cộng dồn bằng cập nhật SQL atomic kèm điều kiện `quantity + requestedQuantity <= 100`; kiểm tra số hàng cập nhật. Nếu chưa tồn tại, INSERT và dựa vào unique active `(cart_id, sku_id, active_marker)` để bắt race; chỉ retry **nội bộ transaction chưa commit** sau lỗi duplicate/deadlock, không retry HTTP POST mù quáng. Các transaction phải giữ thứ tự khóa thống nhất và có retry hữu hạn. Khi quá số lần retry, trả `409 CART_CONCURRENT_MODIFICATION`; nếu vượt 100, trả `409 CART_QUANTITY_LIMIT_EXCEEDED`.
6. Không giữ hàng, không tính tổng tiền authoritative khi thêm giỏ.

**Lỗi trong phạm vi Cart:** `400` invalid UUID/quantity, `401`, `403`, `409` quantity vượt 100 hoặc tranh chấp cập nhật không giải quyết được, `422` SKU không tồn tại/không sellable, `503` Shop không xác minh được, `500` lỗi nội bộ. Mã HTTP `409`/`422` là baseline của Cart; quy chuẩn Error Contract dùng chung vẫn phải được nhóm xác nhận trước khi tích hợp.

**Tránh gửi POST lặp:** `POST /api/cart/items` là thao tác **cộng dồn, không idempotent**. Nếu client không nhận được response do mất kết nối sau commit, tuyệt đối không tự động gửi lại POST chỉ dựa vào timeout. Client GET Cart để xác định trạng thái và yêu cầu người dùng quyết định; thiết kế idempotency key dành cho POST nếu team muốn bảo đảm retry an toàn xuyên HTTP, hiện **chưa thuộc contract đã chốt**.

**Lỗi Shop khi tạo response sau commit:** Việc xác minh SKU trước ghi là bắt buộc. Sau commit, nếu truy vấn Shop để bổ sung giá/trạng thái cho `CartResponse` bị timeout, **vẫn trả `200` với dữ liệu Cart đã lưu**, `availabilityStatus=UNKNOWN`, `priceUnavailable=true`, `estimatedUnitPrice=null` cho SKU chưa xác minh được; không biến commit thành lỗi `503`. Nếu response không thể chuyển tới client, áp dụng hướng dẫn không retry mù quáng ở trên.

### 3.3. `PATCH /api/cart/items/{itemId}`

**Permission:** `CART_MANAGE_SELF`  
**Request:**

```json
{ "quantity": 5, "expectedVersion": 4 }
```

**Thành công:** `200 OK`, trả `CartResponse` sau commit; lỗi Shop khi lấy giá để dựng response xử lý giống POST (không báo thất bại giả).

**Quy tắc:**

- PATCH **đặt quantity bằng giá trị mới**, không cộng dồn.
- Chỉ truy vấn item thuộc Cart của Customer đang xác thực, `deleted_at IS NULL`.
- `expectedVersion` là số nguyên không âm, bắt buộc. Client lấy từ `CartItemResponse.version` của lần đọc gần nhất; thiếu/sai kiểu trả `400`.
- Quantity là số nguyên `[1,100]`; `0`, số âm, số thập phân hoặc trên 100 đều bị từ chối.
- Bắt buộc cập nhật theo điều kiện `item_id`, `cart.owner_id`, `deleted_at IS NULL`, `version = expectedVersion`; cập nhật `quantity`, `updated_at` và `version = version + 1` **atomic** trong một transaction. Số hàng cập nhật bằng 0: trả `404` nếu item không tồn tại/không thuộc owner/đã xóa, còn item vẫn active nhưng version khác: `409 CART_CONCURRENT_MODIFICATION`; không trả dữ liệu owner khác.
- PATCH đổi sang đúng quantity hiện tại là no-op nếu version khớp, không tăng version; version không khớp vẫn `409`.
- Tăng quantity: cần Shop xác minh SKU sellable. Shop timeout hoặc không sellable thì từ chối tăng.
- Giảm quantity: được phép dù Shop không phản hồi; không gọi Shop để chặn giảm.
- Không tự retry PATCH bằng version mới và ghi đè ý định của client. Khi `409`, client đọc lại Cart, hiển thị giá trị mới và chủ động gửi yêu cầu mới.

**Lỗi trong phạm vi Cart:** `400`, `401`, `403`, `404` (item không tồn tại **hoặc không thuộc chủ giỏ**), `409` xung đột version, `422` SKU không sellable khi tăng, `503` Shop timeout khi tăng, `500`.

### 3.4. `DELETE /api/cart/items/{itemId}`

**Permission:** `CART_MANAGE_SELF`  
**Request body:** Không  
**Thành công:** `204 No Content`.

- Soft-delete bằng `deleted_at` và cập nhật `version`; không xóa cứng bản ghi.
- Chỉ tác động trên Cart của Customer đã xác thực.
- DELETE lặp lại trên item **của chính user, đã soft-delete**, trả `204` (idempotent). Item của user khác hoặc ID không thể xác minh thuộc chủ giỏ trả `404` để tránh lộ dữ liệu.
- Không phụ thuộc Shop.

**Lỗi trong phạm vi Cart:** `400` ID không hợp lệ, `401`, `403`, `404`, `500`.

### 3.5. `DELETE /api/cart/items`

**Permission:** `CART_MANAGE_SELF`  
**Request body:** Không  
**Thành công:** `204 No Content`.

- Soft-delete tất cả active CartItem của Customer đang xác thực, không xóa bản ghi `cart` và không ảnh hưởng Order cũ.
- Cart chưa tồn tại hoặc rỗng vẫn trả `204`.
- Không phụ thuộc Shop. Cần cập nhật `version` đối với các item bị xóa, thực hiện trong transaction.

**Lỗi trong phạm vi Cart:** `401`, `403`, `500`.

## 4. API nội bộ và hợp đồng giữa service

### 4.1. Order → Cart: đọc các item được chọn (đề xuất payload, endpoint theo D.2)

**Đường dẫn theo D.2:** `GET /api/internal/carts/{userId}/items?ids=...`  
**Người gọi:** Order Service đã xác thực ở tầng service-to-service; không public trên Gateway.

**Yêu cầu:** `ids` là tập UUID của các CartItem Customer chọn. `userId` trong path phải là user đã được Order xác thực và kiểm tra quyền checkout; Cart vẫn kiểm tra ownership tại DB.

**Đề xuất response `200 OK` (Order cần xác nhận trước tích hợp):**

```json
{
  "userId": "7cde4d7b-53df-45b4-8ba5-f8ff3e256b4a",
  "items": [
    {
      "cartItemId": "a91b46e2-8ef2-4ac1-9d15-3bd3c7c9a201",
      "skuId": "23e4567e-e89b-42d3-a456-426614174000",
      "quantity": 2,
      "version": 4
    }
  ]
}
```

- Trả snapshot **chỉ** cho item active thuộc đúng Cart và user; không trả giá authoritative.
- Nếu bất kỳ `ids` nào không tồn tại, đã xóa hoặc không thuộc Cart của user, **đề xuất từ chối toàn bộ**, không trả kết quả thiếu item một cách âm thầm (`404`/`409` theo lý do).
- Không nhận `userId` do browser gửi làm bằng chứng sở hữu.
- Order phải kiểm tra lại SKU, giá, tồn kho và reserve qua Shop trong luồng checkout, theo UC-CHK-001.
- Contract này cần được Order team duyệt vì `version` được bổ sung để đáp ứng D.8-06.

### 4.2. Cart → Shop: tra cứu SKU và giá hiện tại (đề xuất tích hợp, chưa xác nhận từ Shop)

**Đường dẫn theo D.2:** `POST /api/internal/skus:batch-get`  
**Người gọi:** Cart Service có xác thực nội bộ.

**Request đề xuất:**

```json
{
  "skuIds": ["23e4567e-e89b-42d3-a456-426614174000"]
}
```

**Response đề xuất:**

```json
{
  "items": [
    {
      "skuId": "23e4567e-e89b-42d3-a456-426614174000",
      "sellable": true,
      "currentPrice": 150000.0
    }
  ]
}
```

- Shop là nguồn sellability và current price. Cart không cập nhật dữ liệu này trong DB Cart.
  **Quy tắc diễn giải bắt buộc phía Cart (độc lập với wire format của Shop):**

| Tình huống xác minh                                                                          | Cart diễn giải        | GET Cart                            | POST/tăng quantity                                                        |
| -------------------------------------------------------------------------------------------- | --------------------- | ----------------------------------- | ------------------------------------------------------------------------- |
| Shop xác nhận SKU tồn tại, sellable và có giá                                                | `AVAILABLE`           | Giá tham khảo từ Shop               | Cho phép sau validation                                                   |
| Shop xác nhận SKU ngừng bán/không sellable                                                   | `UNAVAILABLE`         | Giữ item                            | Từ chối `CART_SKU_UNAVAILABLE`                                            |
| Shop xác nhận SKU không tồn tại                                                              | `UNAVAILABLE`         | Giữ item để người dùng biết         | Từ chối `CART_SKU_UNAVAILABLE`                                            |
| Shop timeout, HTTP 5xx, response thiếu SKU mà không nêu lý do hoặc dữ liệu không đủ kết luận | `UNKNOWN`             | `priceUnavailable=true`, giá `null` | Từ chối `CART_SHOP_UNAVAILABLE`                                           |
| SKU có trạng thái xác minh nhưng thiếu giá hợp lệ                                            | Không giả định có giá | Giá `null`, `priceUnavailable=true` | Phải có quy tắc xác nhận sellable riêng; nếu thiếu bằng chứng thì từ chối |

**Ranh giới giao diện:** Cart phải dùng client/adapter để chuyển response Shop thực tế thành kết quả `CONFIRMED_SELLABLE`, `CONFIRMED_UNSELLABLE`, `CONFIRMED_MISSING` hoặc `UNVERIFIED`. Không suy diễn trạng thái từ item vắng mặt. Những tên trạng thái trên là **kiểu xử lý nội bộ Cart**, không áp đặt schema lên Shop.

**Điều kiện để tích hợp:** Shop xác nhận schema batch request, cách báo missing/partial/timeout và cơ chế xác thực service. Nếu chưa có, chỉ kiểm thử Cart qua ShopClient mock; không tuyên bố endpoint đã chạy liên service.

- Hợp đồng request/response trong mục 4.2 mới là **đề xuất của Cart**, chỉ endpoint và mục đích gọi là theo D.2; cần Shop team xác nhận.

### 4.3. Order → Cart: `OrderPlaced` / dọn giỏ sau checkout

D.2 đã mô tả Cart nhận `OrderPlaced` để dọn những item được mua, **nhưng chưa chốt transport** (REST callback/push có retry hay message broker). Do đó **chưa đặt một URL nội bộ giả định làm chuẩn chính thức**.

**Payload logic đề xuất, độc lập transport:**

```json
{
  "orderId": "4b5fda22-bc9d-4f19-9d4f-7231a62073e1",
  "userId": "7cde4d7b-53df-45b4-8ba5-f8ff3e256b4a",
  "purchasedItems": [
    {
      "cartItemId": "a91b46e2-8ef2-4ac1-9d15-3bd3c7c9a201",
      "skuId": "23e4567e-e89b-42d3-a456-426614174000",
      "quantity": 2,
      "version": 4
    }
  ]
}
```

**Xử lý tại Cart trong một transaction:**

1. Xác thực nguồn thông báo Order; không tin payload gửi từ trình duyệt.
2. Bảo đảm `orderId` chỉ được xử lý một lần bằng unique/PK ở `processed_order_event`. `existsByOrderId` trước rồi `INSERT` **không đủ chống race condition**.
3. Với mỗi item, kiểm tra thuộc Cart của `userId` và chỉ soft-delete bằng câu lệnh có điều kiện `id`, `sku_id`, `version`, `deleted_at IS NULL` (và ràng buộc owner qua Cart). Nếu version khác, **giữ item hiện tại**.
4. Ghi nhận `processed_order_event` đã hoàn tất trong cùng transaction với cleanup; transaction lỗi thì rollback cả hai để retry.
5. Nếu thông báo lặp lại sau khi đã xử lý, không dọn Cart lần nữa. Trường hợp một số item đã đổi version là `COMPLETED` về xử lý thông báo, **không có nghĩa mọi item đã bị xóa**.
6. Không xóa những item không có trong `purchasedItems`.

**Điểm cần Order xác nhận (chưa Approved liên service):** thời điểm chính xác phát `OrderPlaced` (sau khi Order thực sự committed), tính bền vững/retry của thông báo, tính toàn vẹn dữ liệu `purchasedItems`, và cách xử lý khi checkout diễn ra song song với thay đổi Cart.

## 5. Bảng mã lỗi dự kiến

| Mã lỗi                         | HTTP đề xuất | Trường hợp                                                        |
| ------------------------------ | -----------: | ----------------------------------------------------------------- |
| `CART_QUANTITY_INVALID`        |          400 | Quantity không phải số nguyên `[1,100]`                           |
| `CART_ITEM_NOT_FOUND`          |          404 | Item không tồn tại, đã xóa hoặc không thuộc chủ giỏ               |
| `CART_QUANTITY_LIMIT_EXCEEDED` |          409 | Tổng quantity sau cộng vượt 100                                   |
| `CART_CONCURRENT_MODIFICATION` |          409 | PATCH có `expectedVersion` không trùng version hiện tại           |
| `CART_SKU_UNAVAILABLE`         |          422 | Shop xác nhận SKU không tồn tại/không sellable khi thêm hoặc tăng |
| `CART_SHOP_UNAVAILABLE`        |          503 | Không xác minh SKU được khi thêm hoặc tăng                        |
| `UNAUTHORIZED`                 |          401 | Chưa xác thực hoặc JWT không hợp lệ                               |
| `FORBIDDEN`                    |          403 | Thiếu quyền Cart tương ứng                                        |
| `INTERNAL_ERROR`               |          500 | Không xử lý được do lỗi nội bộ                                    |

**Baseline đã review cho Cart v1.1:** Các mã và HTTP status ở bảng này. **Chưa chốt ở cấp hệ thống:** shape chuẩn chung; khi có Error Contract của team phải review và đồng bộ trước khi tích hợp. Không dùng thông báo lỗi để tiết lộ Cart của user khác.

## 6. Bất biến dữ liệu, transaction và kiểm thử

- `cart.owner_id` duy nhất cho mỗi Customer theo mô hình Cart hiện tại.
- `cart_item.quantity BETWEEN 1 AND 100` (validate ở API lẫn CHECK tại MySQL).
- `cart_item.deleted_at IS NULL` nghĩa là item đang hoạt động.
- Với MySQL và soft-delete, UNIQUE cho item active được triển khai bằng generated column `active_marker` và `UNIQUE(cart_id, sku_id, active_marker)`; **không** dùng `UNIQUE(cart_id, sku_id, deleted_at)`.
- POST cùng SKU đồng thời: khóa Cart theo owner, cập nhật quantity atomic, unique active item, retry transaction hữu hạn khi duplicate/deadlock; không vượt 100 và không tạo hai active item. Client không retry HTTP POST mù quáng sau timeout.
- PATCH bắt buộc `expectedVersion`, CAS có kiểm tra owner và active item; tăng `version` khi quantity thực sự thay đổi. DELETE/cleanup dùng điều kiện/version atomic.
- GET Cart không ghi dữ liệu; không dùng Shop cache để thay thế giá hiện tại khi Shop lỗi.
- `OrderPlaced` phải idempotent theo `orderId`, xử lý trong transaction cùng cleanup.
- Tất cả truy vấn/mutate client đều nằm trong phạm vi owner xác thực. Cross-user phải bị từ chối, ưu tiên không làm lộ sự tồn tại của item.

**Tối thiểu kiểm thử BlackBox / integration:**

1. GET Cart chưa tạo → `200 {cartId:null,items:[]}` và không insert Cart.
2. POST SKU sellable tạo Cart; POST trùng SKU cộng dồn; đồng thời không tạo trùng.
3. Quantity `0`, âm, thập phân, >100 và tổng sau cộng >100 đều bị từ chối, dữ liệu không thay đổi.
4. PATCH là ghi đè số lượng; tăng cần Shop xác minh, giảm không phụ thuộc Shop.
5. DELETE một item hoặc toàn bộ: soft-delete, lặp lại không gây tác dụng phụ.
6. SKU ngừng bán: giữ CartItem, `UNAVAILABLE`, không cho checkout SKU đó.
7. Shop timeout/partial failure khi GET: đủ item, `UNKNOWN`, `priceUnavailable=true`, `estimatedUnitPrice=null` cho SKU không tra được.
8. Customer A không đọc/sửa/xóa CartItem của Customer B.
9. Order đọc item selected đúng user; không tự lấy giá Cart làm giá authoritative.
10. `OrderPlaced` loại item khớp `version`, giữ item đã sửa, giữ item không mua; retry không xóa lặp.
11. Hai bản `OrderPlaced` cùng `orderId` đồng thời không xử lý hai lần.
12. Hai phiên Web/Mobile GET cùng version; PATCH đầu thành công, PATCH thứ hai trả `409`, không ghi đè; thiếu `expectedVersion` trả `400`.
13. GET Cart mất Shop: `UNKNOWN` và `priceUnavailable` cho SKU chưa xác minh; SKU được Shop xác nhận missing/unavailable thì `UNAVAILABLE`.
14. Batch Shop thiếu một SKU không có lý do: Cart xem SKU đó là `UNKNOWN`, không tự kết luận ngừng bán.

## 7. Mức phê duyệt thiết kế và điều kiện tích hợp

**Trạng thái: APPROVED – baseline thiết kế Cart-owned API Contract v1.1 (chờ review/merge của nhóm).** Có thể dùng làm baseline để triển khai và viết unit/integration test cho Cart. Nhãn này không chứng minh chủ Shop/Order hoặc leader đã phê duyệt hay kiểm thử triển khai thực tế.

**Chưa phê duyệt liên service** cho các phần phụ thuộc dưới đây; vì chưa có xác nhận từ chủ service/ADR, không được ghi giả là đã chốt:

1. **D.2/Q1 – Transport OrderPlaced:** REST callback có retry hoặc message broker. Giữ payload logic độc lập transport; không đặt endpoint callback/messaging mặc định.
2. **Shop – `skus:batch-get`:** Wire format, xử lý SKU không tồn tại, ngừng bán và lỗi một phần. Cart có quy tắc ánh xạ nội bộ tại §4.2; Shop cần xác nhận response cụ thể.
3. **Order – checkout snapshot:** Order nhận, lưu và gửi lại `cartItemId`, `skuId`, `quantity`, `version`; sự kiện chỉ phát sau Order committed. Phải có retry bền vững và idempotency theo `orderId`.
4. **Chuẩn lỗi chung:** Nhóm cần xác nhận shape và HTTP semantics chung. Bảng §5 là baseline nội bộ Cart, không áp đặt cho service khác.
5. **Soft-delete và DB migration:** MySQL generated column `active_marker`, unique constraint và Check phải được thực thi bằng migration, có test duplicate/concurrency; `.dbml` chỉ là mô hình.
6. **Đồng bộ UML (việc cần hoàn tất trước PR):** `CartItemResponse` bổ sung `version`; `UpdateQuantityRequest` bổ sung `expectedVersion`; xuất lại `cart-class.png` và lưu `.drawio`. Chưa có bằng chứng trong lượt review này rằng người dùng đã sửa hai field đó.

**Điều kiện chuyển sang “APPROVED – tích hợp toàn hệ thống”:** Có xác nhận/ADR cho mục (1) đến (4), test hợp đồng với Shop/Order, và cập nhật bản v1.1 nếu interface có thay đổi. Trạng thái hiện tại không thay thế review của chủ Shop, Order hoặc leader.

## 8. Checklist review cuối trước PR

- [x] Năm endpoint và quyền truy cập thống nhất với các quyết định Cart.
- [x] PATCH có `expectedVersion`, response có `version`, quy tắc CAS và `409`.
- [x] Phân biệt Shop lỗi với SKU không bán được và không báo thất bại giả sau commit.
- [x] POST có chiến lược transaction/unique/locking và lưu ý retry không an toàn.
- [x] OrderPlaced idempotent, snapshot cleanup không xóa thay đổi mới.
- [ ] Cập nhật đồng bộ class diagram (`version`, `expectedVersion`) và ảnh xuất.
- [ ] Chủ Shop xác nhận schema batch-get, chủ Order xác nhận snapshot/payload và D.2/Q1 có quyết định transport.
- [ ] Team xác nhận Error Contract dùng chung và review PR.

## 9. Các quy tắc triển khai tránh hiểu nhầm

- **Tính bất biến của snapshot:** `version` phải duy nhất theo từng chuỗi thay đổi của cùng CartItem; không reset khi cập nhật/soft-delete. CartItem được tạo lại sau soft-delete phải có `itemId` mới. So khớp cleanup bằng `itemId`, `skuId`, `version`, owner và active state ngay trong điều kiện update.
- **Idempotency:** `processed_order_event.order_id` có PK/UNIQUE. Xử lý insert và cleanup trong một transaction; nếu insert bị conflict do duplicate thì coi đã xử lý và không chạy cleanup nữa. Không dùng `existsByOrderId()` đơn độc để bảo vệ race.
- **Trình tự checkout:** Order lấy snapshot, xác minh lại SKU/giá/stock và reserve qua Shop; Cart không cam kết giá/stock tại thời điểm checkout. Nếu Order đã đặt và item được Customer sửa sau snapshot, Cart giữ item mới theo D.8-06, không tự trừ quantity.
- **Trường hợp SKU xác nhận ngừng bán:** GET vẫn trả CartItem với `UNAVAILABLE`; `UNKNOWN` dành cho thiếu bằng chứng xác minh. Giá chỉ được hiển thị khi có nguồn Shop hợp lệ.
- **Không lộ Cart khác:** Client endpoints chỉ thao tác dựa trên authenticated principal, không chấp nhận ownerId của client. Internal Order endpoint có service auth + đối chiếu đúng owner với DB.
- **Lưu ý D.1 về soft-delete:** `cart_item` áp dụng soft-delete bằng `deleted_at`; việc xóa bản ghi `cart` không thuộc API M1 và chưa mặc định phát sinh.
