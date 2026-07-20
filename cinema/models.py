from django.db import models
from django.contrib.auth.models import User


# ==========================================
# 1. ManyToManyField (Nhiều - Nhiều)
# Một bộ phim có nhiều thể loại, một thể loại có nhiều bộ phim.
# ==========================================
class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    

class Movie(models.Model):
    title = models.CharField(max_length=255)
    duration = models.IntegerField(help_text="Movie Duration")
    # Django sẽ tự động tạo một bảng trung gian (movie_genres) ở dưới Database
    genres = models.ManyToManyField(Genre, related_name="movies")

    description = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True, help_text="Điểm đánh giá từ 0.0 đến 10.0")
    actors = models.TextField(blank=True, null=True, help_text="Danh sách diễn viên, cách nhau bằng dấu phẩy")

    # upload_to='movies/posters/' sẽ tự động tạo thư mục này và lưu ảnh vào đó
    poster_url = models.ImageField(upload_to='movies/posters/', blank=True, null=True, help_text="Ảnh dọc cho phim")
    banner_url = models.ImageField(upload_to='movies/banners/', blank=True, null=True, help_text="Ảnh ngang làm background")

    def __str__(self):
        return self.title
    

# ==========================================
# 2. ForeignKey (Một - Nhiều)
# Một Rạp có nhiều Phòng, Một Phòng có nhiều Ghế
# ==========================================
class Cinema(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='cinemas/', blank=True, null=True, help_text="Ảnh mặt tiền rạp")

    def __str__(self):
        return self.name
    
class Room(models.Model):
    # on_delete=models.CASCADE: Nếu xóa Rạp, tất cả Phòng thuộc Rạp đó delete
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.cinema.name} - {self.name}"

class Seat(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="seats")
    row = models.CharField(max_length=5)
    number = models.IntegerField()

    class Meta:
        unique_together = ('room', 'row', 'number')

    def __str__(self):
        return f"{self.room.name} - {self.row}{self.number}"
    

class Showtime(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="showtimes")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="showtimes")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Đang chờ thanh toán'),
        ('CONFIRMED', 'Đã xác nhận'),
        ('CANCELLED', 'Đã hủy'),
    ]
    
    # PROTECT: Không cho phép xóa User nếu họ đã có lịch sử Booking (bảo vệ audit)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="bookings")
    showtime = models.ForeignKey(Showtime, on_delete=models.PROTECT, related_name="bookings")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)


class Ticket(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="tickets")
    seat = models.ForeignKey(Seat, on_delete=models.PROTECT)

    class Meta:
        # RẤT QUAN TRỌNG: Không thể có 2 vé cho cùng 1 ghế trong cùng 1 suất chiếu
        # Tuy nhiên, kiểm tra này thường phải làm phức tạp hơn ở mức DB transaction
        # vì Ticket nối với Booking, còn Booking nối với Showtime.
        pass

# ==========================================
# 3. OneToOneField (Một - Một)
# Mỗi Booking chỉ có duy nhất 1 hóa đơn thanh toán và ngược lại
# ==========================================
class Payment(models.Model):
    # Đảm bảo mối quan hệ 1-1, không thể có 2 payment cho 1 booking
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    is_successful = models.BooleanField(default=False)
    paid_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for booking {self.booking.id}"

    