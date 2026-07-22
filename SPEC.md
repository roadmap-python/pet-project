# TÀI LIỆU ĐẶC TẢ KỸ THUẬT DỰ ÁN LUXECINEMA (SPEC.md)

Tài liệu này định nghĩa chi tiết các quy tắc nghiệp vụ, cấu trúc dữ liệu, đặc tả API, trường hợp biên và phạm vi hoạt động của hệ thống đặt vé phim trực tuyến LuxeCinema.

---

## 1. Quy tắc Nghiệp vụ (Business Rules)

### 1.1. Hệ thống Người dùng & Xác thực
- **Xác thực**: Sử dụng cơ chế token JSON Web Token (JWT) thông qua tiêu chuẩn `SimpleJWT` đối với các API. Các trang giao diện HTML sử dụng xác thực Session chuẩn của Django.
- **Phân quyền**:
  - **Khách vãng lai (Public)**: Có quyền truy cập các API đọc dữ liệu (`GET`) bao gồm danh sách phim, chi tiết phim, danh sách rạp, suất chiếu và sơ đồ trạng thái ghế ngồi.
  - **Thành viên đăng nhập (Authenticated)**: Thực hiện chọn ghế, giữ ghế tạm thời, tạo đơn đặt vé (Booking) và thanh toán hóa đơn.
  - **Quản trị viên (Admin)**: Toàn quyền thao tác CRUD (Thêm, Sửa, Xóa) trên Phim, Rạp và Suất chiếu; quản lý và kiểm tra tất cả các đơn đặt vé của hệ thống qua Dashboard.

### 1.2. Nghiệp vụ Giữ Ghế & Đặt Vé (Seat Hold & Booking Lifecycle)
- **Cơ chế Giữ ghế tạm thời (Seat Hold)**:
  - Khi một ghế được click chọn $\rightarrow$ Ghế đó sẽ chuyển sang trạng thái bị giữ (`SeatHold`) bởi chính tài khoản đó trong vòng **đúng 10 phút (600 giây)**.
  - Một ghế đang được giữ bởi `Người dùng A` thì `Người dùng B` không thể chọn (Checkbox bị vô hiệu hóa trên giao diện; gọi API sẽ trả về mã lỗi `409 Conflict`).
  - Nếu người dùng bấm bỏ tích chọn ghế đó $\rightarrow$ Bản ghi giữ ghế bị xóa lập tức, giải phóng ghế cho người khác chọn.
- **Tính đồng nhất thời gian giữ ghế (Session Timer Inheritance)**:
  - Khi người dùng đã có ghế đang giữ, nếu họ bấm chọn thêm các ghế tiếp theo, thời điểm hết hạn của các ghế chọn sau sẽ **kế thừa và đồng bộ** theo mốc thời gian hết hạn của chiếc ghế đầu tiên đã chọn.
- **Quy trình Thanh toán & Hủy tự động (Timeout Enforcement)**:
  - Nhấn *"Tiếp tục thanh toán"* sẽ chuyển đổi danh sách ghế đang giữ thành một đơn đặt vé trạng thái **`PENDING`**.
  - Nếu quá **10 phút** kể từ thời điểm khởi tạo đơn đặt vé PENDING mà người dùng chưa thanh toán:
    - Đơn đặt vé tự động chuyển sang trạng thái **`CANCELLED`**.
    - Các ghế liên kết với đơn hàng đó được giải phóng hoàn toàn (xóa các bản ghi `SeatHold`).
    - Nếu cố tình thanh toán đơn hàng đã quá 10 phút, hệ thống sẽ chặn và trả về lỗi.
  - Khi thanh toán thành công:
    - Trạng thái Booking cập nhật thành **`CONFIRMED`**.
    - Bản ghi giữ ghế `SeatHold` liên quan bị xóa vĩnh viễn (Ghế chuyển sang màu đỏ - Ghế đã bán).

### 1.3. Cơ chế Tính giá Vé (Seat Pricing)
- **Ghế Thường (Standard)**: Áp dụng mức giá gốc của Suất chiếu (`base_price`).
- **Ghế VIP**: Áp dụng đối với các ghế thuộc **hàng E, F, G**. Giá vé ghế VIP bằng giá gốc cộng thêm phụ thu 20% (`base_price * 1.2`).

---

## 2. Đặc tả API Contract

### 2.1. API Xác thực (Authentication)
- **POST `/api/auth/register/`**: Đăng ký tài khoản.
  - *Input*: `full_name`, `phone_number`, `email`, `password`, `confirm_password`
  - *Success (201)*: Trả về thông tin user và cặp token JWT (`access`, `refresh`).
- **POST `/api/auth/login/`**: Đăng nhập lấy token.
  - *Input*: `username`, `password`
  - *Success (200)*: Trả về cặp token JWT.
- **POST `/api/auth/refresh/`**: Làm mới token access.
  - *Input*: `refresh`
  - *Success (200)*: Trả về `access` token mới.

### 2.2. API Phim (Movies)
- **GET `/api/movies/`**: Lấy danh sách phim (Public).
- **POST `/api/movies/`**: Thêm phim mới (Admin).
  - *Input*: `title`, `duration`, `description`, `rating`, `actors`, `genres` (danh sách ID thể loại).
- **GET `/api/movies/{movie_id}/`**: Lấy chi tiết bộ phim.
- **PUT `/api/movies/{movie_id}/`**: Cập nhật bộ phim (Admin).
- **DELETE `/api/movies/{movie_id}/`**: Xóa phim (Admin, phản hồi `204`).

### 2.3. API Rạp chiếu (Cinemas)
- **GET `/api/cinemas/`**: Danh sách rạp chiếu.
- **POST `/api/cinemas/`**: Thêm rạp mới (Admin).
- **GET `/api/cinemas/{cinema_id}/`**: Chi tiết rạp kèm danh sách phòng chiếu.
- **PUT `/api/cinemas/{cinema_id}/`**: Cập nhật rạp (Admin).
- **DELETE `/api/cinemas/{cinema_id}/`**: Xóa rạp (Admin, phản hồi `204`).

### 2.4. API Suất chiếu & Sơ đồ Ghế (Showtimes & Seats)
- **GET `/api/showtimes/`**: Lấy danh sách lịch chiếu.
- **POST `/api/showtimes/`**: Tạo suất chiếu mới (Admin).
- **GET `/api/showtimes/{showtime_id}/seats/`**: Sơ đồ ghế thực tế (Real-Time Seat Map).
  - *Success (200)*: Trả về danh sách ghế kèm thuộc tính `is_booked` (bao gồm đã bán chính thức hoặc đang bị giữ bởi người khác).

### 2.5. API Đặt Vé & Thanh Toán (Bookings & Payments)
- **POST `/api/bookings/`**: Tạo đơn hàng chờ thanh toán (PENDING).
  - *Input*: `showtime_id`, `selected_seat_ids` (mảng ID các ghế muốn chọn).
  - *Success (201)*: Trả về chi tiết đơn đặt vé và tổng tiền.
- **POST `/api/bookings/{booking_id}/pay/`**: Xác nhận thanh toán (Chuyển sang CONFIRMED).
  - *Success (200)*: Cập nhật hóa đơn thành công và xóa bỏ giữ ghế tạm thời.

---

## 3. Các Trường Hợp Biên (Edge Cases)

| Tình huống biên | Cách xử lý của hệ thống |
| :--- | :--- |
| **Hai người dùng chọn cùng một ghế cùng một lúc** | Hệ thống dùng CSDL transaction chặn người chọn sau và trả về mã lỗi `409 Conflict`. Người dùng sau sẽ nhận được thông báo đỏ: *"Ghế đã được người khác giữ chỗ!"* |
| **Quay lại trang chọn ghế khi chưa thanh toán** | Đơn hàng `PENDING` cũ của chính người dùng đó trên suất chiếu này sẽ tự động bị xóa bỏ để nhường chỗ cho phiên chọn ghế mới. Ghế cũ vẫn có thể bỏ chọn hoặc chọn lại bình thường. |
| **Tải lại trang chọn ghế hoặc trình duyệt bị tắt đột ngột** | Khi người dùng quay lại trang trước thời hạn 10 phút, hệ thống tính toán chính xác số giây còn lại và hiển thị đồng hồ đếm ngược chạy tiếp (ví dụ: `06:30` còn lại) chứ không đặt lại từ đầu. |
| **Cố thanh toán sau khi đơn hàng đã quá hạn 10 phút** | Hệ thống so khớp thời gian tạo đơn hàng, nếu quá 10 phút sẽ tự động hủy đơn (`CANCELLED`), giải phóng ghế và từ chối xử lý thanh toán, đưa người dùng về lại trang chọn ghế kèm thông báo lỗi. |

---

## 4. Phạm vi Không Thực hiện (Out of Scope)
- **Tích hợp cổng thanh toán thực tế**: Toàn bộ luồng thanh toán được giả lập xác thực qua ngân hàng ảo (luôn phản hồi thành công khi nhấn nút thanh toán trên môi trường phát triển).
- **Tự động hoàn tiền**: Dự án không hỗ trợ quy trình hoàn tiền tự động khi đơn hàng đã chuyển sang trạng thái `CONFIRMED`.
- **Thay đổi sơ đồ ghế động**: Sơ đồ ghế ngồi của phòng chiếu là cố định sau khi được thiết lập lúc khởi tạo phòng (Room), không hỗ trợ thay đổi cấu hình vị trí ghế động theo từng suất chiếu.
- **Hủy vé thủ công từ phía thành viên**: Thành viên không có quyền tự hủy các vé đã mua thành công (`CONFIRMED`). Việc hủy vé chỉ được phép thực hiện bởi Admin hệ thống.
