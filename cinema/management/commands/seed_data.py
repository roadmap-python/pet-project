import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from cinema.models import Genre, Movie, Cinema, Room, Seat, Showtime, Booking, Ticket, Payment, SeatHold
from pathlib import Path
import json

MOVIE_DATA = [
    {
        "title": "Avengers: Doomsday",
        "poster": "https://m.media-amazon.com/images/M/MV5BM2E1ZTJiZTgtZGI2Zi00MzAxLThhZjktMmU3M2E3Yzk3NjUxXkEyXkFqcGc@.*V1*.jpg",
        "description": "The Avengers reunite to face a new cosmic threat that could destroy multiple realities and reshape the future of humanity.",
        "rating": 8.9,
        "actors": [
            "Robert Downey Jr.",
            "Chris Hemsworth",
            "Tom Holland"
        ]
    },
    {
        "title": "Avengers: Endgame",
        "poster": "https://m.media-amazon.com/images/M/MV5BMTc5MDE2ODcwNV5BMl5BanBnXkFtZTgwMzI2NzQ2NzM@.*V1*.jpg",
        "description": "The remaining Avengers assemble for one final mission to reverse Thanos' devastating actions and restore balance to the universe.",
        "rating": 8.4,
        "actors": [
            "Robert Downey Jr.",
            "Chris Evans",
            "Scarlett Johansson"
        ]
    },
    {
        "title": "The Avengers",
        "poster": "https://m.media-amazon.com/images/M/MV5BNGE0YTVjNzUtNzJjOS00NGNlLTgxMzctZTY4YTE1Y2Y1ZTU4XkEyXkFqcGc@.*V1*.jpg",
        "description": "Earth's mightiest heroes join forces to stop Loki and his alien army from conquering the planet.",
        "rating": 8.0,
        "actors": [
            "Robert Downey Jr.",
            "Chris Evans",
            "Mark Ruffalo"
        ]
    },
    {
        "title": "Avengers: Infinity War",
        "poster": "https://m.media-amazon.com/images/M/MV5BMjMxNjY2MDU1OV5BMl5BanBnXkFtZTgwNzY1MTUwNTM@.*V1*.jpg",
        "description": "The Avengers and their allies must stop Thanos from collecting all six Infinity Stones.",
        "rating": 8.4,
        "actors": [
            "Robert Downey Jr.",
            "Chris Hemsworth",
            "Josh Brolin"
        ]
    },
    {
        "title": "Avengers: Age of Ultron",
        "poster": "https://m.media-amazon.com/images/M/MV5BODBhYTg1NGQtNGVmNS00ZTdiLThjYTYtZDFkNzRiNTZmNDZjXkEyXkFqcGc@.*V1*.jpg",
        "description": "The Avengers battle the rogue AI Ultron, who seeks to eradicate humanity in the name of peace.",
        "rating": 7.3,
        "actors": [
            "Robert Downey Jr.",
            "Chris Evans",
            "James Spader"
        ]
    },
    {
        "title": "Doraemon (1979)",
        "poster": "https://m.media-amazon.com/images/M/MV5BOTE4ZjlkOWYtZDViYy00ZmZlLTkyMmQtZjNiNTBjMzBiNDA0XkEyXkFqcGc@.*V1*.jpg",
        "description": "A robotic cat from the future helps a young boy named Nobita overcome everyday challenges with magical gadgets.",
        "rating": 8.1,
        "actors": [
            "Nobuyo Oyama",
            "Noriko Ohara",
            "Michiko Nomura"
        ]
    },
    {
        "title": "Pokémon",
        "poster": "https://m.media-amazon.com/images/M/MV5BMzE0ZDU1MzQtNTNlYS00YjNlLWE2ODktZmFmNDYzMTBlZTBmXkEyXkFqcGc@.*V1*.jpg",
        "description": "Ash Ketchum travels the world with Pikachu, striving to become a Pokémon Master.",
        "rating": 7.5,
        "actors": [
            "Veronica Taylor",
            "Rachael Lillis",
            "Eric Stuart"
        ]
    },
    {
        "title": "Demon Slayer: Kimetsu no Yaiba",
        "poster": "https://m.media-amazon.com/images/M/MV5BMWU1OGEwNmQtNGM3MS00YTYyLThmYmMtN2FjYzQzNzNmNTE0XkEyXkFqcGc@.*V1*.jpg",
        "description": "Tanjiro Kamado fights demons while searching for a cure for his sister Nezuko.",
        "rating": 8.7,
        "actors": [
            "Natsuki Hanae",
            "Akari Kito",
            "Hiro Shimono"
        ]
    },
    {
        "title": "Spider-Man: No Way Home",
        "poster": "https://m.media-amazon.com/images/M/MV5BMmFiZGZjMmEtMTA0Ni00MzA2LTljMTYtZGI2MGJmZWYzZTQ2XkEyXkFqcGc@.*V1*.jpg",
        "description": "Spider-Man faces villains from multiple universes after a spell goes wrong.",
        "rating": 8.2,
        "actors": [
            "Tom Holland",
            "Zendaya",
            "Benedict Cumberbatch"
        ]
    },
    {
        "title": "Spider-Man: Across the Spider-Verse",
        "poster": "https://m.media-amazon.com/images/M/MV5BNThiZjA3MjItZGY5Ni00ZmJhLWEwN2EtOTBlYTA4Y2E0M2ZmXkEyXkFqcGc@.*V1*.jpg",
        "description": "Miles Morales embarks on an epic adventure across the multiverse with Spider-People from different dimensions.",
        "rating": 8.6,
        "actors": [
            "Shameik Moore",
            "Hailee Steinfeld",
            "Oscar Isaac"
        ]
    },
    {
        "title": "Avatar: The Way of Water",
        "poster": "https://m.media-amazon.com/images/M/MV5BNWI0Y2NkOWEtMmM2OC00MjQ3LWI1YzItZGQxYzQ3NzI4NWZmXkEyXkFqcGc@.*V1*.jpg",
        "description": "Jake Sully and Neytiri protect their family while exploring the oceans of Pandora.",
        "rating": 7.8,
        "actors": [
            "Sam Worthington",
            "Zoe Saldana",
            "Sigourney Weaver"
        ]
    },
    {
        "title": "Avatar: The Last Airbender",
        "poster": "https://m.media-amazon.com/images/M/MV5BY2Y5OTM0MDAtOWZkNS00MWIyLWIxMzItYzY3ODljMTY3ODNlXkEyXkFqcGc@.*V1*.jpg",
        "description": "A young Avatar must master all four elements to bring peace to a world divided by war.",
        "rating": 9.3,
        "actors": [
            "Zach Tyler Eisen",
            "Mae Whitman",
            "Jack De Sena"
        ]
    }
]

class Command(BaseCommand):
    help = 'Nạp dữ liệu nhanh (Fast Seed) thẳng vào Database không tải file'

    @transaction.atomic
    def handle(self, *args, **kwargs):

        self.stdout.write("1. Cleared old data...")
        SeatHold.objects.all().delete()
        Payment.objects.all().delete()
        Ticket.objects.all().delete()
        Booking.objects.all().delete()
        Showtime.objects.all().delete()
        Seat.objects.all().delete()
        Room.objects.all().delete()
        Cinema.objects.all().delete()
        Movie.objects.all().delete()
        Genre.objects.all().delete()

        self.stdout.write("2. Created Genres...")
        genre_names = ['Hành Động', 'Viễn Tưởng', 'Hoạt Hình', 'Phiêu Lưu', 'Tâm Lý']
        genres = [Genre.objects.create(name=name) for name in genre_names]

        self.stdout.write("3. Created Movies...")
        movies = []
        for data in MOVIE_DATA:
            movie = Movie.objects.create(
                title=data["title"],
                duration=random.choice([100, 120, 150, 180]),
                poster_url=data["poster"],  # Đẩy thẳng chuỗi URL tĩnh vào DB
                description=data["description"],
                rating=data["rating"]
            )
            movie.genres.set(random.sample(genres, random.randint(1, 3)))
            movies.append(movie)

        self.stdout.write("4. Created Cinemas and Rooms...")
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

        self.stdout.write("5. Created Seat Matrix...")
        seats = []
        for room in rooms:
            for row in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']: 
                for num in range(1, 15):
                    seats.append(Seat(room=room, row=row, number=num))
        Seat.objects.bulk_create(seats, batch_size=500)
        
        self.stdout.write("6. Created Showtimes...")
        now = timezone.now()
        showtimes = []
        for room in rooms:
            for day_offset in range(7):
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
        self.stdout.write(self.style.SUCCESS("Success: Seeding completed successfully."))