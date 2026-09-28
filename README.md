# EeasyShopping — E-Commerce Platform

> Project áp dụng quy trình Scrum, phát triển bởi nhóm 3 thành viên.

## Giới thiệu

**Mục tiêu dự án:**
Xây dựng nền tảng Thương mại điện tử, giúp người dùng có thể tiếp cận với các mặt hàng theo sở thích, nhu cầu - tìm kiếm, xem sản phẩm, đặt hàng và thanh toán

**Đối tượng người dùng:**
Khách hàng đang tìm kiếm mặt hàng theo nhu cầu, sở thích.
Người bán đăng sản phẩm và admin quản lý hệ thống

---

## Thành viên & Vai trò

| Tên | Vai trò Scrum | Vai trò kỹ thuật | GitHub |
|---|---|---|---|
| Nguyễn Phú Quý | Product Owner | Developer | @NgPhuQuy |
| Phạm Hoàng Phúc | Scrum Master | Developer | @PhamPhuc0903 |
| Nguyễn Châu Hoàng Khang | Developer | Developer | @Ryannguyxn |

---

## Quy tắc & Quy trình làm việc
 
**Quy trình quản lý:** Scrum, sprint 1 tuần. Task được quản lý trên Jira, tài liệu chi tiết lưu ở Confluence.
 
**Branch strategy:** Git Flow — main / dev / feat/* / hotfix/*
 
**Quy tắc commit:** Conventional Commits — feat:, fix:, docs:, refactor:
 
**Coding convention:**  Naming class/method theo chuẩn Java, format code trước khi commit 
 
**Quy trình Pull Request:**
1. Tạo branch từ `dev`: `feat/ten-tinh-nang`
2. Code + test local
3. Push và tạo Pull Request, mô tả rõ thay đổi
4. Merge vào `develop`
5. Ít nhất 1 thành viên khác review trước khi merge
6. Merge vào `main` để tự động deploy lên staging

---

## Pipeline CI/CD

Do hệ thống chia theo kiến trúc microservice và tách biệt Frontend/Backend, mỗi service (và FE) có pipeline CI/CD riêng, chạy độc lập — chỉ trigger khi có thay đổi trong đúng thư mục/service đó, không build lại toàn bộ hệ thống mỗi lần push.

**CI** (áp dụng riêng cho từng service/FE)
- Chạy tự động khi có push lên bất kỳ nhánh nào (trừ `main` — không push trực tiếp lên `main` được, phải qua Pull Request)
- Gồm các bước: build project, chạy unit/integration test tự động, chạy lint check format code — chỉ chạy cho service có thay đổi
- Mục đích: phát hiện lỗi sớm trước khi merge, không ảnh hưởng đến các service khác

**CD** (áp dụng riêng cho từng service/FE)
- Chạy tự động khi Pull Request được merge vào `main`
- Gồm các bước: build lại, chạy test, đóng gói (build image/artifact) — riêng cho service vừa thay đổi
- Deploy lên production: thực hiện thủ công (chưa tự động deploy), deploy độc lập từng service, không cần deploy lại toàn bộ hệ thống

---

## Công nghệ sử dụng

### Frontend
- Framework: ReactJS(Vite)
- UI Library: TailwingCSS

### Backend
- Framework: Spring Boot 3
- Ngôn ngữ: Java
- Authentication: JWT

### Database
- Hệ quản trị: MySQL
- ORM: Hibernate

### DevOps / CI-CD
- Container: Docker, Docker Compose
- CI/CD Pipeline: GitHub Actions
- Deploy: ...

### Công cụ quản lý
- Quản lý task: Jira
- Tài liệu: Confluence
- Giao tiếp: Zalo group

---

## Kiến trúc hệ thống

Hệ thống sử dụng kiến trúc microservice với framework Spring Boot, vì tính mở rộng và thay đổi yêu cầu linh hoạt. Phù hợp với các hệ thống enterprise cần được thường xuyên mở rộng, bảo trì, thay đổi các công nghệ mới một cách linh hoạt.

---

## Cấu trúc thư mục

```
E-Commerce/
├── E-Commerce-Web/
│   └── ...
├── E-Commerce-APIs/
│   └── ...
└── README.md
└── .gitignore
```

---

## Testing

- Loại test: Unit test, Integration test
- Công cụ: JUnit, Mockito 
- Cách chạy test: ...

---

## Sprint Log

| Sprint | Thời gian | Mục tiêu | Kết quả |
|---|---|---|---|
| Sprint 0 | 28/08/2026 - 05/09/2026 | Xác định rõ các mục tiêu cần đạt trong project | |
| Sprint 1 | ngày - ngày | | |
| Sprint 2 | ngày - ngày | | |

---

## Tài liệu liên quan

- Jira Board: [link jira Board](https://ngphuquy-e-commerce.atlassian.net/jira/software/projects/SCRUM/boards/1?filter=&groupBy=none&atlOrigin=eyJpIjoiMTBmOGU0YjUxNjViNGY1OTk2OThlOWE2MjE2YjQ2MTciLCJwIjoiaiJ9)
- Figma Design: [link]