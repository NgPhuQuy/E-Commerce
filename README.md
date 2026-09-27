# EeasyShopping — E-Commerce Platform

> Side project áp dụng quy trình Scrum, phát triển bởi nhóm 3 thành viên.

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
| Nguyễn Phú Quý | Product Owner | Developer | [@NgPhuQuy] |
| Phạm Hoàng Phúc | Scrum Master | Developer | [@PhamPhuc0903] |
| Nguyễn Châu Hoàng Khang | Developer | Developer | [@Ryannguyxn] |

---

## Quy tắc & Quy trình làm việc
 
**Quy trình quản lý:** Scrum, sprint 1 tuần. Task được quản lý trên Jira, tài liệu chi tiết lưu ở Confluence.
 
**Branch strategy:** Git Flow — main / develop / feature/* / hotfix/*
 
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
 
**CI**
- Chạy tự động khi có push lên bất kỳ nhánh nào (trừ `main` — không push trực tiếp lên `main` được, phải qua Pull Request)
- Gồm các bước: build project, chạy unit test tự động, chạy lint check format code
- Mục đích: phát hiện lỗi sớm trước khi merge
**CD**
- Chạy tự động khi Pull Request được merge vào `main`
- Gồm các bước: build lại, chạy test, đóng gói (build image/artifact)
- Deploy lên production: thực hiện thủ công (chưa tự động deploy)

---

## Công nghệ sử dụng

### Frontend
- Framework: 
- UI Library:
- State management:

### Backend
- Framework: Spring boot 3
- Ngôn ngữ: Java
- Authentication: JWT

### Database
- Hệ quản trị: MySQL
- ORM: Hibernate

### DevOps / CI-CD
- Container: Docker, Docker Compose
- CI/CD Pipeline: Github Actions
- Deploy: ...

### Công cụ quản lý
- Quản lý task: Jira 
- Tài liệu: Confluence
- Giao tiếp: Zalo group

---

## Kiến trúc hệ thống
Hệ thống sử dụng kiến trúc microservice với framework Spring boot, vì tính mở rộng và thay đổi yêu cầu linh hoạt. Phù hợp với các hệ thống enterprise cần được thường xuyên mở rộng, bảo trì, thay đổi các công nghệ mới một cách linh hoạt.

---

## 📂 Cấu trúc thư mục

```
project-root/
├── frontend/
│   └── ...
├── backend/
│   └── ...
├── docs/
│   └── ...
└── README.md
```

---

## 🔄 Quy trình phát triển (Workflow)

**Quy trình quản lý:** Scrum, sprint 1 tuần

**Branch strategy:** <!-- vd: Git Flow — main / develop / feature/* / hotfix/* -->

**Quy tắc commit:** <!-- vd: Conventional Commits — feat:, fix:, docs:, refactor: -->

**Quy trình Pull Request:**
1. Tạo branch từ `develop`: `feature/ten-tinh-nang`
2. Code + tự test local
3. Push và tạo Pull Request, mô tả rõ thay đổi
4. Ít nhất 1 thành viên khác review trước khi merge
5. Merge vào `develop`, sau đó merge vào `main` khi release

---

## 🧪 Testing

- Loại test: <!-- vd: Unit test, Integration test -->
- Công cụ: <!-- vd: Pytest, Jest -->
- Cách chạy test:
```bash
[lệnh chạy test]
```

---

## 📅 Sprint Log

| Sprint | Thời gian | Mục tiêu | Kết quả |
|---|---|---|---|
| Sprint 0 | [ngày - ngày] | Setup môi trường, tech stack, CI/CD | |
| Sprint 1 | [ngày - ngày] | | |
| Sprint 2 | [ngày - ngày] | | |

---

## 📖 Tài liệu liên quan

- Jira Board: [link]
- Confluence Docs: [link]
- Figma Design: [link]

---
