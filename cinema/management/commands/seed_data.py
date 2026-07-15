import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from cinema.models import Genre, Movie, Cinema, Room, Seat, Showtime

MOVIE_DATA = [
    {"title": "Avengers: Doomsday", "poster": "https://m.media-amazon.com/images/M/MV5BM2E1ZTJiZTgtZGI2Zi00MzAxLThhZjktMmU3M2E3Yzk3NjUxXkEyXkFqcGc@._V1_.jpg"},
    {"title": "Avengers: Endgame", "poster": "https://m.media-amazon.com/images/M/MV5BMTc5MDE2ODcwNV5BMl5BanBnXkFtZTgwMzI2NzQ2NzM@._V1_.jpg"},
    {"title": "The Avengers", "poster": "https://m.media-amazon.com/images/M/MV5BNGE0YTVjNzUtNzJjOS00NGNlLTgxMzctZTY4YTE1Y2Y1ZTU4XkEyXkFqcGc@._V1_.jpg"},
    {"title": "Avengers: Infinity War", "poster": "https://m.media-amazon.com/images/M/MV5BMjMxNjY2MDU1OV5BMl5BanBnXkFtZTgwNzY1MTUwNTM@._V1_.jpg"},
    {"title": "Avengers: Age of Ultron", "poster": "https://m.media-amazon.com/images/M/MV5BODBhYTg1NGQtNGVmNS00ZTdiLThjYTYtZDFkNzRiNTZmNDZjXkEyXkFqcGc@._V1_.jpg"},
    {"title": "Doraemon (1979)", "poster": "https://m.media-amazon.com/images/M/MV5BOTE4ZjlkOWYtZDViYy00ZmZlLTkyMmQtZjNiNTBjMzBiNDA0XkEyXkFqcGc@._V1_.jpg"},
    {"title": "Pokémon", "poster": "https://m.media-amazon.com/images/M/MV5BMzE0ZDU1MzQtNTNlYS00YjNlLWE2ODktZmFmNDYzMTBlZTBmXkEyXkFqcGc@._V1_.jpg"},
    {"title": "Demon Slayer: Kimetsu no Yaiba", "poster": "https://m.media-amazon.com/images/M/MV5BMWU1OGEwNmQtNGM3MS00YTYyLThmYmMtN2FjYzQzNzNmNTE0XkEyXkFqcGc@._V1_.jpg"},
    {"title": "Spider-Man: No Way Home", "poster": "https://m.media-amazon.com/images/M/MV5BMmFiZGZjMmEtMTA0Ni00MzA2LTljMTYtZGI2MGJmZWYzZTQ2XkEyXkFqcGc@._V1_.jpg"},
    {"title": "Spider-Man: Across the Spider-Verse", "poster": "https://m.media-amazon.com/images/M/MV5BNThiZjA3MjItZGY5Ni00ZmJhLWEwN2EtOTBlYTA4Y2E0M2ZmXkEyXkFqcGc@._V1_.jpg"},
    {"title": "Avatar: The Way of Water", "poster": "https://m.media-amazon.com/images/M/MV5BNWI0Y2NkOWEtMmM2OC00MjQ3LWI1YzItZGQxYzQ3NzI4NWZmXkEyXkFqcGc@._V1_.jpg"},
    {"title": "Avatar: The Last Airbender", "poster": "https://m.media-amazon.com/images/M/MV5BY2Y5OTM0MDAtOWZkNS00MWIyLWIxMzItYzY3ODljMTY3ODNlXkEyXkFqcGc@._V1_.jpg"}
]

class Command(BaseCommand):
    help = 'Nạp dữ liệu nhanh (Fast Seed) thẳng vào Database không tải file'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("1. Dọn dẹp dữ liệu cũ...")
        Showtime.objects.all().delete()
        Seat.objects.all().delete()
        Room.objects.all().delete()
        Cinema.objects.all().delete()
        Movie.objects.all().delete()
        Genre.objects.all().delete()

        self.stdout.write("2. Khởi tạo Thể loại (Genres)...")
        genre_names = ['Hành Động', 'Viễn Tưởng', 'Hoạt Hình', 'Phiêu Lưu', 'Tâm Lý']
        genres = [Genre.objects.create(name=name) for name in genre_names]

        self.stdout.write("3. Đang nạp Phim (Lưu trực tiếp URL vào DB)...")
        movies = []
        for data in MOVIE_DATA:
            movie = Movie.objects.create(
                title=data["title"],
                duration=random.choice([100, 120, 150, 180]),
                poster_url=data["poster"]  # Đẩy thẳng chuỗi URL tĩnh vào DB
            )
            movie.genres.set(random.sample(genres, random.randint(1, 3)))
            movies.append(movie)

        self.stdout.write("4. Sinh hệ thống Rạp và Phòng chiếu...")
        cinema_data = [
            ("CGV Vincom Đồng Khởi", "Q1, TP.HCM"), 
            ("Lotte Cinema Nam Sài Gòn", "Q7, TP.HCM"),
            ("Galaxy Nguyễn Du", "Q1, TP.HCM"),
            ("BHD Star Phạm Ngọc Thạch", "Đống Đa, HN")
        ]
        rooms = []
        for name, location in cinema_data:
            cinema = Cinema.objects.create(name=name, location=location)
            for i in range(1, 5):
                rooms.append(Room.objects.create(cinema=cinema, name=f"Cinema {i}"))

        self.stdout.write("5. Sinh hệ thống Ma trận Ghế ngồi hàng loạt...")
        seats = []
        for room in rooms:
            for row in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']: 
                for num in range(1, 15):
                    seats.append(Seat(room=room, row=row, number=num))
        Seat.objects.bulk_create(seats, batch_size=500)
        
        self.stdout.write("6. Lên Lịch chiếu (Showtimes) cho 3 ngày tới...")
        now = timezone.now()
        showtimes = []
        for room in rooms:
            for day_offset in range(3):
                current_time = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
                end_of_day = current_time.replace(hour=23, minute=0)

                while current_time < end_of_day:
                    movie = random.choice(movies)
                    start_time = current_time
                    end_time = start_time + timedelta(minutes=movie.duration)
                    
                    showtimes.append(Showtime(
                        movie=movie,
                        room=room,
                        start_time=start_time,
                        end_time=end_time,
                        base_price=random.choice([100000, 120000, 150000])
                    ))
                    current_time = end_time + timedelta(minutes=30)

        Showtime.objects.bulk_create(showtimes, batch_size=500)
        self.stdout.write(self.style.SUCCESS("🎉 HOÀN TẤT! Dữ liệu đã được nạp siêu tốc."))