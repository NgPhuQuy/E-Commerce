# Hướng dẫn sử dụng Docker — EeasyShopping

**Phiên bản:** v0.1 · **Ngày:** 16/11/2026
**Liên quan:** D.11 (`docs/design/11-deployment/README.md`), `docker-compose.yml`, `docker-compose.ci.yml`

Tài liệu này dành cho thành viên mới: cách chạy hệ thống bằng Docker, các lệnh hay dùng, ý nghĩa các cờ (flag) và cách xử lý lỗi thường gặp.

> **Quy tắc quan trọng nhất:** mọi lệnh `docker compose ...` chạy từ **thư mục gốc của repo** (nơi có `docker-compose.yml`).

---

## 1. Khái niệm cần biết

| Thuật ngữ | Nghĩa |
|---|---|
| **Image** | Bản đóng gói sẵn của một phần mềm (ví dụ `mysql:8.4`), giống file cài đặt |
| **Container** | Image đang chạy, giống chương trình đang mở. Xóa container thì dữ liệu bên trong mất |
| **Volume** | Ổ lưu dữ liệu nằm ngoài container, giữ lại dữ liệu khi container bị xóa |
| **Network** | Mạng ảo nối các container. Container gọi nhau bằng **tên service** (ví dụ `mysql`, `auth-service`) |
| **Compose** | Công cụ đọc `docker-compose.yml` để dựng cả hệ thống bằng một lệnh |
| **Healthcheck** | Lệnh tự kiểm tra "container đã khỏe chưa". Trạng thái: `starting` → `healthy` / `unhealthy` |

---

## 2. Cài đặt và kiểm tra

1. Cài **Docker Desktop** (Windows/macOS) và mở lên, chờ đến khi báo *Engine running*.
2. Kiểm tra:
   ```bash
   docker --version
   docker compose version     # nên từ 2.24 trở lên (bản CI dùng !override / !reset)
   docker run --rm hello-world
   ```

---

## 3. Chạy lần đầu

```bash
# 1. Tạo file biến môi trường thật từ mẫu
cp .env.example .env          # Windows PowerShell: Copy-Item .env.example .env
# 2. Mở .env và điền giá trị (mật khẩu, khóa...). KHÔNG commit file này.

# 3. Kiểm tra cú pháp và biến
docker compose config -q      # im lặng = đúng

# 4. Dựng toàn bộ hệ thống và chờ mọi container khỏe
docker compose up -d --build --wait

# 5. Xem trạng thái
docker compose ps
```

Lần đầu sẽ chậm vì phải tải image và build. Các lần sau nhanh hơn nhờ cache.

---

## 4. Cấu trúc liên quan

```
E-Commerce/
├── docker-compose.yml        # cấu hình chạy chính (local / staging)
├── docker-compose.ci.yml     # ghi đè thêm cho CI (WireMock, Mailpit, tmpfs)
├── .env.example              # mẫu biến môi trường (COMMIT)
├── .env.ci                   # biến giả lập cho CI (COMMIT)
├── .env                      # biến thật trên máy bạn (KHÔNG commit)
├── docker/
│   ├── Dockerfile.template   # Dockerfile dùng chung cho các service
│   ├── mysql/init/           # script tạo schema + user MySQL
│   └── mocks/wiremock/       # route giả lập Google, VNPay cho CI
└── services/                 # mã nguồn từng service
```

---

## 5. Các lệnh thường dùng

### 5.1 Chạy và dừng

| Mục đích | Lệnh |
|---|---|
| Chạy cả hệ thống, build lại, chờ khỏe | `docker compose up -d --build --wait` |
| Chạy chỉ một vài service (và phần chúng phụ thuộc) | `docker compose up -d --wait mysql minio` |
| Build lại và chạy lại **một** service sau khi sửa code | `docker compose up -d --build auth-service` |
| Dừng, **giữ** dữ liệu | `docker compose down` |
| Dừng và **xóa cả dữ liệu** (volume) | `docker compose down -v` |
| Dừng tạm (không xóa container) | `docker compose stop` |
| Bật lại container đã dừng | `docker compose start` |
| Khởi động lại một service | `docker compose restart auth-service` |

### 5.2 Xem trạng thái và log

| Mục đích | Lệnh |
|---|---|
| Xem container nào đang chạy, khỏe hay chưa | `docker compose ps` |
| Xem cả container đã thoát (ví dụ `minio-init`) | `docker compose ps -a` |
| Xem log một service | `docker compose logs auth-service` |
| Theo dõi log trực tiếp, chỉ lấy 100 dòng cuối | `docker compose logs -f --tail=100 auth-service` |
| Xem log toàn bộ hệ thống | `docker compose logs -f --tail=50` |
| Xem cấu hình sau khi đã thay biến `${...}` | `docker compose config` |
| Xem CPU/RAM từng container | `docker stats` |

### 5.3 Vào bên trong container

| Mục đích | Lệnh |
|---|---|
| Vào console MySQL (nhập mật khẩu root khi được hỏi) | `docker compose exec mysql mysql -uroot -p` |
| Vào một database bằng user riêng của service | `docker compose exec mysql mysql -uauth_user -p auth_db` |
| Chạy một câu SQL rồi thoát | `docker compose exec mysql mysql -uroot -p<mật_khẩu> -e "SHOW DATABASES;"` |
| Mở shell trong một container | `docker compose exec auth-service sh` |

Trong console MySQL: `SHOW DATABASES;`, `USE auth_db;`, `SHOW TABLES;`, `exit`.

### 5.4 Build và dọn dẹp

| Mục đích | Lệnh |
|---|---|
| Build lại image, **bỏ cache** (khi nghi ngờ build cũ) | `docker compose build --no-cache auth-service` |
| Ép tạo lại container dù cấu hình không đổi | `docker compose up -d --force-recreate auth-service` |
| Tải lại image mới nhất theo tag | `docker compose pull` |
| Xóa container "mồ côi" của service đã bỏ khỏi compose | `docker compose down --remove-orphans` |
| Xem dung lượng Docker đang chiếm | `docker system df` |
| Dọn image không dùng (cẩn thận, xem mục 9) | `docker image prune` |

---

## 6. Ý nghĩa các cờ (flag)

| Cờ | Ở lệnh | Nghĩa |
|---|---|---|
| `-d` | `up` | Chạy nền (detached), trả lại terminal cho bạn |
| `--build` | `up` | Build lại image trước khi chạy |
| `--wait` | `up` | Chờ cho đến khi mọi container **healthy** rồi mới kết thúc; nếu có container lỗi thì trả mã lỗi (ngụ ý `-d`) |
| `--force-recreate` | `up` | Tạo lại container dù cấu hình không đổi |
| `-v` | `down` | **Xóa luôn volume** (mất dữ liệu DB, MinIO) |
| `--remove-orphans` | `down`, `up` | Xóa container không còn khai báo trong compose |
| `--no-cache` | `build` | Build không dùng cache |
| `-f` | **đứng sau `docker compose`** | Chỉ định file compose: `docker compose -f a.yml -f b.yml ...` |
| `-f` | **đứng sau `logs`** | Theo dõi log liên tục (follow). Hai cờ `-f` này khác nhau hoàn toàn |
| `--tail=N` | `logs` | Chỉ lấy N dòng cuối |
| `--env-file` | `docker compose` | Dùng file biến khác thay cho `.env` mặc định |
| `-q` | `config` | Chỉ kiểm tra, không in nội dung |

---

## 7. Tình huống thường gặp

**Sửa code một service và muốn chạy lại**
```bash
docker compose up -d --build <tên-service>
docker compose logs -f --tail=100 <tên-service>
```

**Sửa `.env`**
Compose đọc `.env` lúc chạy `up`, nên cần tạo lại container:
```bash
docker compose up -d
```
(`docker compose restart` **không** nạp lại `.env`.)

**Sửa script init MySQL (`docker/mysql/init/`)**
Script chỉ chạy khi volume còn trống, nên phải xóa volume:
```bash
docker compose down -v
docker compose up -d --wait mysql
```

**Reset sạch toàn bộ để làm lại từ đầu**
```bash
docker compose down -v
docker compose up -d --build --wait
```

**Kiểm tra dữ liệu không mất sau khi restart**
```bash
docker compose down           # KHÔNG có -v
docker compose up -d --wait
```

**Chạy bản CI (có WireMock và Mailpit, DB sạch mỗi lần)**
```bash
docker compose -f docker-compose.yml -f docker-compose.ci.yml --env-file .env.ci up -d --build --wait
docker compose -f docker-compose.yml -f docker-compose.ci.yml --env-file .env.ci down -v
```

**Thêm service mới vào compose**
1. Copy block mẫu "KHUNG THÊM SERVICE" trong `docker-compose.yml`, đổi tên, `context`, tên schema, cổng host.
2. Khai `depends_on` với `condition: service_healthy` cho các service/DB nó phụ thuộc.
3. Thêm schema và user vào `docker/mysql/init/01-init-schemas.sh` (nếu có DB riêng) và biến tương ứng vào `.env.example`.
4. `docker compose config -q` để kiểm tra rồi `docker compose up -d --build <tên-service>`.

---

## 8. Địa chỉ và cổng (trên máy bạn)

Các cổng của service con chỉ bind vào `127.0.0.1`, người khác trong mạng LAN không truy cập được.

| Thành phần | Địa chỉ | Ghi chú |
|---|---|---|
| `api-gateway` | `http://localhost:8080` | Điểm vào duy nhất của hệ thống (khi đã thêm service) |
| Các service con | `127.0.0.1:8081` … `8087` | auth, shop, cart, order, payment, notification, audit (khi đã thêm) |
| MinIO API | `http://localhost:9000` | Dùng bởi `shop-service` |
| MinIO Console | `http://localhost:9001` | Đăng nhập bằng `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |
| Mailpit UI (chỉ CI) | `http://localhost:8025` | Đọc mail test |
| MySQL | **không mở ra máy host** | Mạng `eeasy-data-net` là `internal`. Dùng `docker compose exec mysql ...` |

Hai service gọi nhau trong Docker dùng **tên service**, ví dụ `http://auth-service:8080` (cổng 8080 là cổng trong container), không dùng `localhost`.

---

## 9. Quy tắc làm việc nhóm

- **Không commit `.env`.** Chỉ commit `.env.example` và `.env.ci`.
- **Cẩn thận với `down -v`:** nó xóa dữ liệu DB và MinIO trên máy bạn.
- **Không dùng `docker system prune -a`** nếu chưa hiểu: lệnh này xóa cả image của dự án khác trên máy.
- Mật khẩu trong `.env` không chứa dấu nháy `'` `"` hoặc ký tự `$`.
- File `.sh` phải lưu kiểu xuống dòng **LF** (không phải CRLF), nếu không MySQL init sẽ lỗi.
- Trước khi mở PR sửa compose: chạy `docker compose config -q`, rồi `docker compose up -d --build --wait` từ đầu (sau `down -v`) để chắc chắn dựng được từ trạng thái sạch.

---

## 10. Xử lý lỗi thường gặp

| Triệu chứng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| `cannot connect to the Docker daemon` | Docker Desktop chưa chạy xong | Mở Docker Desktop, chờ *Engine running* |
| `no configuration file provided: not found` | Đang đứng sai thư mục | `cd` về gốc repo |
| `The "X" variable is not set` | `.env` thiếu biến hoặc không nằm cạnh compose | Đối chiếu với `.env.example` |
| `TLS handshake timeout` khi tải image | Mạng chập chờn tới Docker Hub | Thử lại; đổi DNS; dùng `registry-mirrors` trong Docker Engine settings |
| Container `unhealthy` | Ứng dụng lỗi khi khởi động hoặc healthcheck sai | `docker compose logs <tên>` để xem lỗi |
| `--wait` báo lỗi hoặc quá hạn | Một container không khỏe | `docker compose ps` để biết cái nào, rồi xem log của nó |
| `port is already allocated` | Cổng đang bị chương trình khác dùng | Windows: `netstat -ano \| findstr :8080`; hoặc đổi cổng host trong `.env` |
| Sửa script init mà không thấy đổi | Volume cũ vẫn còn | `docker compose down -v` rồi `up` lại |
| Script `.sh` báo lỗi lạ (ví dụ `\r: command not found`) | File bị xuống dòng CRLF | Đổi sang LF, thêm `*.sh text eol=lf` vào `.gitattributes` |
| `service "mysql" is not running` khi `exec` | Container chưa chạy hoặc đã thoát | `docker compose ps -a`, rồi `up -d` lại |
| Service không kết nối được DB | Dùng `localhost` thay vì tên service `mysql` | Sửa `SPRING_DATASOURCE_URL` trỏ `mysql:3306` |
| Ổ đĩa đầy do Docker | Image, cache build tích lũy | `docker system df` để xem; `docker builder prune` để dọn cache build |

**Lưu ý PowerShell và Git Bash:** cách xử lý dấu nháy khác nhau. Lệnh có `-e "SQL..."` nên dùng nháy kép bao ngoài, không bọc thêm nháy đơn.

---

## 11. Tham khảo

- D.11 — Sơ đồ thành phần và thiết kế triển khai: `docs/design/11-deployment/README.md`
- Dockerfile dùng chung: `docker/Dockerfile.template`
- Tài liệu Docker Compose: https://docs.docker.com/compose/