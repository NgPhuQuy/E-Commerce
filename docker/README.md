# Dockerfile Template - EeasyShopping

## 1. Mục đích

Cung cấp Dockerfile multi-stage dùng chung cho các backend service Spring Boot của EeasyShopping.

Template sử dụng Java 25, Maven Wrapper, JRE runtime và chạy container bằng non-root user.

## 2. Cấu trúc

- `docker/Dockerfile.template`: Dockerfile dùng chung.
- `examples/sample-service/`: Spring Boot service tối thiểu để kiểm thử template.
- `examples/sample-service/.dockerignore`: Cấu hình loại trừ file khỏi Docker build context.

## 3. Yêu cầu sử dụng

Mỗi service sử dụng template cần có:

- Java 25 và Maven Wrapper được cấu hình trong project.
- `pom.xml`, `mvnw`, `.mvn/` và `src/`.
- Spring Boot Actuator cung cấp endpoint `/actuator/health`.
- Ứng dụng lắng nghe trên cổng 8080.

Nếu service có cấu trúc, cổng hoặc health endpoint khác, cần điều chỉnh Dockerfile tương ứng.

## 4. Build image mẫu

Chạy tại thư mục gốc repository:

```bash
docker build -f docker/Dockerfile.template -t sample-service:1.2 ./examples/sample-service
```

## 5. Chạy container

```bash
docker run -d --name sample-service-test -p 8080:8080 sample-service:1.2
```

## 6. Kiểm thử

Kiểm tra health endpoint:

```bash
curl http://localhost:8080/actuator/health
```

Kết quả mong đợi:

```json
{ "status": "UP" }
```

Kiểm tra Docker HEALTHCHECK:

```bash
docker inspect --format '{{.State.Health.Status}}' sample-service-test
```

Kết quả mong đợi: `healthy`.

Kiểm tra non-root user:

```bash
docker exec sample-service-test id
```

UID phải khác 0.

## 7. Kiểm thử Maven

Chạy tại thư mục `examples/sample-service/`:

Windows:

```powershell
.\mvnw.cmd test
```

Linux/macOS:

```bash
./mvnw test
```

## 8. Lưu ý

- Build stage sử dụng JDK 25 và Maven Wrapper.
- Runtime stage sử dụng JRE 25.
- Không đưa `.env`, secrets hoặc thư mục `target/` vào Docker build context.
- Dockerfile hiện đóng gói ứng dụng với `-DskipTests`; cần chạy test riêng trước khi merge.
- Template dành cho các Spring Boot service, không áp dụng trực tiếp cho React hoặc Flutter.
- Sample service chỉ dùng để kiểm thử hạ tầng, không phải service nghiệp vụ của hệ thống.
- Jira SCRUM-185 mô tả endpoint `/health`; phiên bản mẫu sử dụng `/actuator/health` theo hướng dẫn kỹ thuật. Khác biệt này cần được reviewer xác nhận.
