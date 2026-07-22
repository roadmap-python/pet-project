# LuxeCinema - Movie Ticket Booking System

Hệ thống đặt vé phim trực tuyến cao cấp được xây dựng trên nền tảng **Django (Python)** kết hợp **Django Rest Framework (DRF)**, giao diện được thiết kế hiện đại, mượt mà bằng **TailwindCSS** và xử lý tương tác thời gian thực bằng **Alpine.js**.

---

## 1. Các Tính Năng Nổi Bật

- **Xác thực & Bảo mật**: Hỗ trợ đồng thời đăng nhập bằng Session (cho Web UI) và JWT Token (cho RESTful APIs).
- **Luồng Đặt Vé Động 3 Bước**: Chọn Rạp $\rightarrow$ Chọn Suất Chiếu $\rightarrow$ Chọn Ghế Ngồi.
- **Giữ Ghế Thời Gian Thực (10 Phút)**:
  - Khóa giữ chỗ tạm thời trong 10 phút ngay khi người dùng chọn ghế.
  - Đồng hồ đếm ngược trực quan hiển thị thời gian còn lại của phiên.
  - Tự động hủy đơn hàng và giải phóng ghế nếu quá hạn 10 phút chưa thanh toán.
  - Đồng bộ trạng thái ghế bị người khác giữ bằng cơ chế Short Polling (3 giây/lần).
- **Trang Quản Trị Cao Cấp (Admin Dashboard)**: Quản lý phim, rạp, phòng chiếu, lịch chiếu, và kiểm tra doanh thu, trạng thái đặt vé kèm bộ lọc thông minh.
- **Đặc tả RESTful API & Swagger**:
  - Giao diện Swagger UI tương tác trực tiếp tích hợp sẵn.
  - Đặc tả API chuẩn OpenAPI 3.0.

---

## 2. Hướng Dẫn Cài Đặt và Chạy Dự Án

### Cách 1: Khởi chạy bằng Docker (Khuyên dùng)

Yêu cầu máy tính của bạn đã cài đặt Docker và Docker Compose.

1. **Khởi dựng và chạy container (Build & Run)**:
   Lệnh này sẽ tự động tải các gói thư viện hệ thống, cài đặt dependencies, chạy migrations, nạp dữ liệu mẫu seed_data và khởi chạy máy chủ:
   ```bash
   docker-compose up --build
   ```

2. **Chạy ứng dụng dưới chế độ chạy nền (Detached mode)**:
   ```bash
   docker-compose up -d
   ```

3. **Dừng container và dọn dẹp tài nguyên**:
   ```bash
   docker-compose down
   ```

---

### Cách 2: Khởi chạy trực tiếp trên máy cục bộ (Local)

#### Bước 1: Chuẩn bị môi trường ảo
Mở terminal tại thư mục gốc của dự án và kích hoạt môi trường ảo:

```bash
# Trên Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Trên Windows (CMD):
.venv\Scripts\activate.bat

# Trên macOS/Linux:
source .venv/bin/activate
```

### Bước 2: Cập nhật thư viện
Cài đặt các gói phụ thuộc cần thiết cho dự án:
```bash
pip install -r requirements.txt
```

### Bước 3: Đồng bộ Cơ sở dữ liệu (Migrations)
Tạo bảng và thiết lập các mối liên kết quan hệ trong SQLite:
```bash
python manage.py makemigrations cinema
python manage.py migrate
```

### Bước 4: Tạo tài khoản Admin hệ thống
Tạo tài khoản quản trị viên tối cao để đăng nhập vào trang Dashboard và Admin Django:
```bash
python manage.py createsuperuser
```
*(Nhập Email, Tên tài khoản và Mật khẩu theo hướng dẫn)*

### Bước 5: Nạp dữ liệu mẫu siêu tốc (Seeding Data)
Hệ thống hỗ trợ lệnh Seeding mẫu để tạo nhanh Phim, Thể loại, Rạp, Phòng chiếu, sơ đồ Ghế ngồi và hàng loạt Suất chiếu tự động cho 7 ngày tới:
```bash
python manage.py seed_data
```

### Bước 6: Khởi chạy Máy chủ Development
```bash
python manage.py runserver
```

---

## 3. Các Địa Chỉ Truy Cập Quan Trọng

Sau khi máy chủ khởi động thành công, bạn có thể truy cập các đường dẫn sau:

- **Giao diện đặt vé (Homepage)**: [http://localhost:8000/](http://localhost:8000/)
- **Tài liệu API tương tác (Swagger UI Docs)**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **Trang Quản lý Dashboard Admin**: [http://localhost:8000/manage/dashboard/](http://localhost:8000/manage/dashboard/)
- **File OpenAPI gốc (YAML)**: [http://localhost:8000/openapi.yaml](http://localhost:8000/openapi.yaml)
- **Django Admin Mặc định**: [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

## 4. Chạy Kiểm Thử Tự Động (Unit Tests)

Dự án đi kèm bộ test case tự động bao quát toàn bộ các luồng xác thực JWT, thao tác CRUD Phim/Rạp/Suất chiếu, Sơ đồ ghế ngồi và luồng đặt vé thanh toán bảo mật. Chạy bộ kiểm thử bằng lệnh:

```bash
python manage.py test cinema
```

---

## 5. Đo Lường Độ Bao Phủ Kiểm Thử (Unit Test Coverage - Gate 2)

Hệ thống yêu cầu độ bao phủ kiểm thử (test coverage) đạt ít nhất **≥ 60%** trên phần logic nghiệp vụ cốt lõi (Core Business Logic) nằm tại hai tệp tin `cinema/models.py` và `cinema/api_views.py`.

### Quy trình chạy và xuất báo cáo:

1. **Chạy kiểm thử và thu thập dữ liệu độ bao phủ**:
   ```bash
   coverage run --source=cinema manage.py test cinema
   ```

2. **Xuất báo cáo chi tiết cho phần Business Logic**:
   ```bash
   coverage report --include="cinema/models.py,cinema/api_views.py"
   ```

   *Kết quả thực tế*: Phần logic cốt lõi đạt tỷ lệ bao phủ **67%** (vượt chỉ tiêu tối thiểu 60% của Gate 2).

3. **Xuất báo cáo dưới dạng giao diện HTML** (Tùy chọn):
   ```bash
   coverage html
   ```
   Sau đó, mở tệp `htmlcov/index.html` bằng trình duyệt để xem báo cáo trực quan từng dòng code được bao phủ.
