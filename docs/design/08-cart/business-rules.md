# Quy tắc nghiệp vụ – Cart Service

**Dự án:** EeasyShopping  
**Task:** SCRUM-191 – D.8 Thiết kế gói Cart Service  
**Phạm vi:** Milestone 1  
**Trạng thái:** Bản nháp, chờ review

## 1. Tài liệu tham chiếu

- `docs/QUY_UOC_KY_THUAT.md` (D.1)
- `docs/design/02-boundaries.md` (D.2)
- `docs/design/Milestone_1/EeasyShopping_M1_Use_Case_Specifications.docx` (D.3)
- `docs/design/Milestone_1/EeasyShopping_M1_Permission_Matrix.docx`
- `docs/Requirements_Analysis&Specification.docx`

**Use Case:** UC-CART-001 – Customer quản lý Cart và CartItem.

**Yêu cầu liên quan:** FR-CART-001, FR-CART-002, FR-CART-003, FR-CART-004.

## 2. Phạm vi trách nhiệm

### 2.1. Cart Service chịu trách nhiệm

- Quản lý giỏ hàng và các CartItem.
- Thêm, xem, cập nhật số lượng và xóa CartItem.
- Kiểm tra quyền sở hữu giỏ hàng của Customer.
- Lưu SKU ID và số lượng của từng CartItem.
- Loại bỏ các CartItem đã được mua sau khi nhận thông báo OrderPlaced hợp lệ.

### 2.2. Cart Service không chịu trách nhiệm

- Quản lý Product, SKU hoặc Inventory.
- Lưu giá sản phẩm chính thức.
- Quyết định trạng thái bán hàng của SKU.
- Tạo Order hoặc xử lý Payment.
- Giữ hàng hoặc trừ tồn kho khi thêm sản phẩm vào giỏ.

Shop Service cung cấp thông tin SKU, trạng thái bán và giá hiện tại.

Order Service điều phối checkout, kiểm tra lại giá và tồn kho trước khi tạo đơn hàng.

## 3. Các quy tắc nghiệp vụ đã chốt trong D.8

### D.8-01 – Thêm trùng SKU

Khi Customer thêm SKU đã có trong giỏ, hệ thống cộng dồn số lượng thay vì tạo CartItem mới.

Ví dụ: Giỏ có 2 đơn vị SKU A, thêm 3 đơn vị thì số lượng mới bằng 5.

Ràng buộc:

- Một Cart không có hai CartItem đang hoạt động cùng SKU.
- Request đồng thời không được tạo bản ghi trùng.
- Tổng số lượng sau khi cộng phải được kiểm tra giới hạn.

### D.8-02 – Kiểm tra số lượng

Số lượng của CartItem phải là số nguyên dương.

- `quantity > 0`: Hợp lệ nếu không vượt giới hạn.
- `quantity = 0`: Từ chối.
- `quantity < 0`: Từ chối.
- Số thập phân hoặc dữ liệu không phải số nguyên: Từ chối.

Muốn loại bỏ sản phẩm khỏi giỏ phải sử dụng API DELETE riêng.

### D.8-03 – Giới hạn số lượng

Mỗi SKU được có tối đa 100 đơn vị trong Cart.

Giới hạn áp dụng cho tổng quantity sau khi thêm hoặc cập nhật.

Ví dụ: Đang có 80 đơn vị, thêm 30 đơn vị thì request bị từ chối và số lượng vẫn là 80.

Cart không giữ hàng hoặc bảo đảm tồn kho. Checkout phải kiểm tra lại với Shop Service.

### D.8-04 – SKU ngừng bán

Khi SKU đã có trong Cart nhưng ngừng bán:

- Giữ nguyên CartItem.
- Khi lấy được thông tin từ Shop, đánh dấu SKU là `unavailable` trong response.
- Không cho phép checkout SKU không khả dụng.
- Customer vẫn có thể xóa CartItem.

Trạng thái bán hàng thuộc Shop Service, không được lưu trong Cart DB như dữ liệu authoritative.

### D.8-05 – Shop Service không phản hồi

Khi Shop Service timeout hoặc tạm thời không khả dụng:

- GET Cart vẫn trả `skuId` và `quantity`.
- Thông tin giá hiện tại được đánh dấu `priceUnavailable`.
- Không sử dụng giá cũ làm giá hiện tại.
- Không cho phép thêm SKU mới.
- Không cho phép tăng số lượng CartItem.
- Vẫn cho phép giảm số lượng hoặc xóa CartItem.

### D.8-06 – Dọn Cart sau khi đặt hàng

Khi nhận được thông báo `OrderPlaced` hợp lệ:

- Chỉ xử lý những CartItem được chọn mua.
- Không ảnh hưởng đến các CartItem không được chọn.
- Chỉ xóa CartItem nếu trạng thái hiện tại còn khớp với snapshot lúc checkout.
- Bảo toàn thay đổi mới của Customer sau thời điểm checkout.

Cơ chế so khớp snapshot và version sẽ được mô tả chi tiết trong thiết kế dữ liệu và API nội bộ.

### D.8-07 – Chống xử lý lặp OrderPlaced

Việc xử lý `OrderPlaced` phải có tính idempotent theo `orderId`.

- Cùng một Order không được khiến Cart bị dọn nhiều lần.
- Phải ghi nhận Order đã xử lý.
- Kiểm tra trùng lặp và cập nhật Cart phải bảo đảm tính nhất quán trong transaction.

Cơ chế truyền thông báo giữa Order và Cart chưa được chốt ở D.2 nên không mặc định sử dụng RabbitMQ hoặc công nghệ cụ thể.

### D.8-08 – Khởi tạo Cart khi cần (Lazy Creation)

Cart chỉ được tạo khi Customer thêm SKU đầu tiên thành công.

- GET Cart khi chưa tồn tại: Trả giỏ rỗng, không ghi database.
- POST thêm SKU đầu tiên: Tạo Cart và CartItem trong cùng transaction.
- Mỗi Customer có tối đa một Cart đang hoạt động.
- Request thêm SKU đồng thời không được tạo nhiều Cart cho một Customer.

## 4. Phân quyền

### 4.1. Quyền truy cập

- `CART_READ_SELF`: Xem giỏ hàng của chính mình.
- `CART_MANAGE_SELF`: Thêm, cập nhật và xóa CartItem của chính mình.

### 4.2. Quy tắc bảo mật

- Guest không được thao tác Cart.
- Customer chỉ truy cập Cart thuộc chính mình.
- Backend xác định `userId` từ thông tin xác thực.
- Không tin `userId` hoặc `cartId` do client gửi để xác định quyền sở hữu.
- Seller và Admin không mặc nhiên được xem giỏ của Customer khác.
- API nội bộ dành cho Order Service phải có cơ chế xác thực và phân quyền giữa các service.

## 5. Các vấn đề kỹ thuật cần hoàn thiện

- Thiết kế ERD và ràng buộc duy nhất.
- Chính sách soft-delete cho CartItem.
- Cơ chế xử lý concurrent requests.
- Trường `version` và cách đối chiếu snapshot.
- Thiết kế lưu thông tin `orderId` đã xử lý.
- Request/response và mã lỗi của các API.
- Cơ chế truyền `OrderPlaced` giữa Order và Cart.

## 6. Truy vết yêu cầu

| Quy tắc           | Căn cứ                                          |
| ----------------- | ----------------------------------------------- |
| D.8-01 đến D.8-03 | FR-CART-001/002, UC-CART-001 và quyết định D.8  |
| D.8-04, D.8-05    | FR-CART-004, D.2, UC-CART-001 và quyết định D.8 |
| D.8-06, D.8-07    | D.2 và quyết định D.8                           |
| D.8-08            | Quyết định thiết kế D.8                         |
| Phân quyền        | FR-CART-003 và Permission Matrix M1             |

**Lưu ý:** Các mã D.8-01 đến D.8-08 là quyết định thiết kế của task SCRUM-191, không phải mã Business Rule gốc trong Requirements Specification.
