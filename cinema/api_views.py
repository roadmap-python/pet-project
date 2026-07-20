import json
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Genre, Movie, Cinema, Room, Seat, Showtime, Booking, Ticket, Payment

# Helper function to serialize a movie
def serialize_movie(movie):
    return {
        'id': movie.id,
        'title': movie.title,
        'duration': movie.duration,
        'description': movie.description,
        'rating': float(movie.rating) if movie.rating else 0.0,
        'actors': movie.actors,
        'genres': [genre.name for genre in movie.genres.all()],
        'poster_url': movie.poster_url.url if movie.poster_url else None,
        'banner_url': movie.banner_url.url if movie.banner_url else None
    }

# Helper function to serialize a booking
def serialize_booking(booking):
    return {
        'id': booking.id,
        'username': booking.user.username,
        'showtime': {
            'id': booking.showtime.id,
            'movie': booking.showtime.movie.title,
            'room': booking.showtime.room.name,
            'cinema': booking.showtime.room.cinema.name,
            'start_time': booking.showtime.start_time.isoformat(),
        },
        'status': booking.status,
        'tickets': [
            {'seat': f"{ticket.seat.row}{ticket.seat.number}", 'price': float(booking.showtime.base_price * Decimal('1.20') if ticket.seat.row in ['E', 'F', 'G'] else booking.showtime.base_price)}
            for ticket in booking.tickets.all()
        ],
        'total_amount': float(booking.payment.amount) if hasattr(booking, 'payment') else 0.0,
        'created_at': booking.created_at.isoformat()
    }


# ==========================================
# AUTHENTICATION API
# ==========================================
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        full_name = request.data.get('full_name')
        phone_number = request.data.get('phone_number')
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if not full_name or not phone_number or not email or not password or not confirm_password:
            return Response({'error': 'Vui lòng điền đầy đủ thông tin'}, status=status.HTTP_400_BAD_REQUEST)
            
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            return Response({'error': 'Email đã tồn tại'}, status=status.HTTP_400_BAD_REQUEST)
            
        if password != confirm_password:
            return Response({'error': 'Mật khẩu không khớp'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.create_user(
            username=email, 
            email=email, 
            password=password,
            first_name=full_name
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Đăng ký tài khoản thành công!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


# ==========================================
# MOVIE API
# ==========================================
class MovieListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        movies = Movie.objects.all().order_by('-id')
        data = [serialize_movie(m) for m in movies]
        return Response({'movies': data}, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            title = request.data.get('title')
            duration = request.data.get('duration')
            description = request.data.get('description', '')
            rating = request.data.get('rating', 0.0)
            actors = request.data.get('actors', '')
            
            if not title or not duration:
                return Response({'error': 'Title and duration are required fields.'}, status=status.HTTP_400_BAD_REQUEST)
                
            movie = Movie.objects.create(
                title=title,
                duration=int(duration),
                description=description,
                rating=Decimal(str(rating)),
                actors=actors
            )
            
            # Handle genres if provided
            genre_ids = request.data.get('genres', [])
            if genre_ids:
                movie.genres.set(Genre.objects.filter(id__in=genre_ids))
                
            return Response(serialize_movie(movie), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MovieDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)
        return Response(serialize_movie(movie), status=status.HTTP_200_OK)

    def put(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)
        try:
            movie.title = request.data.get('title', movie.title)
            movie.duration = int(request.data.get('duration', movie.duration))
            movie.description = request.data.get('description', movie.description)
            movie.rating = Decimal(str(request.data.get('rating', movie.rating)))
            movie.actors = request.data.get('actors', movie.actors)
            movie.save()
            
            genre_ids = request.data.get('genres')
            if genre_ids is not None:
                movie.genres.set(Genre.objects.filter(id__in=genre_ids))
                
            return Response(serialize_movie(movie), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)
        movie.delete()
        return Response({'message': 'Movie deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


# ==========================================
# CINEMA API
# ==========================================
class CinemaListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cinemas = Cinema.objects.all().order_by('name')
        data = [{
            'id': c.id,
            'name': c.name,
            'location': c.location,
            'image': c.image.url if c.image else None
        } for c in cinemas]
        return Response({'cinemas': data}, status=status.HTTP_200_OK)


# ==========================================
# SHOWTIME API
# ==========================================
class ShowtimeListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        showtimes = Showtime.objects.all().order_by('start_time')
        data = [{
            'id': s.id,
            'movie': s.movie.title,
            'movie_id': s.movie.id,
            'room': s.room.name,
            'cinema': s.room.cinema.name,
            'start_time': s.start_time.isoformat(),
            'end_time': s.end_time.isoformat(),
            'base_price': float(s.base_price)
        } for s in showtimes]
        return Response({'showtimes': data}, status=status.HTTP_200_OK)


# ==========================================
# BOOKING API
# ==========================================
class BookingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):      
        bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
        data = [serialize_booking(b) for b in bookings]
        return Response({'bookings': data}, status=status.HTTP_200_OK)

    def post(self, request):           
        try:
            showtime_id = request.data.get('showtime_id')
            selected_seat_ids = request.data.get('selected_seat_ids', [])
            
            if not showtime_id or not selected_seat_ids:
                return Response({'error': 'showtime_id and selected_seat_ids are required.'}, status=status.HTTP_400_BAD_REQUEST)
                
            showtime = get_object_or_404(Showtime, id=showtime_id)
            
            with transaction.atomic():
                # Check for double booking
                booked_seats = Ticket.objects.filter(
                    booking__showtime=showtime,
                    booking__status__in=['CONFIRMED', 'PENDING'],
                    seat_id__in=selected_seat_ids
                )
                if booked_seats.exists():
                    return Response({'error': 'Một hoặc nhiều ghế đã được đặt trước đó.'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Create Booking
                booking = Booking.objects.create(
                    user=request.user,
                    showtime=showtime,
                    status='PENDING'
                )
                
                # Create tickets and calculate total amount
                total_amount = 0
                for seat_id in selected_seat_ids:
                    seat = Seat.objects.get(id=seat_id)
                    Ticket.objects.create(booking=booking, seat=seat)
                    
                    price = showtime.base_price
                    if seat.row in ['E', 'F', 'G']:
                        price = price * Decimal('1.20')
                    total_amount += price
                
                # Create Payment draft
                Payment.objects.create(
                    booking=booking,
                    amount=total_amount,
                    is_successful=False
                )
                
            return Response(serialize_booking(booking), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
