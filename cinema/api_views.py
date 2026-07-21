import json
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
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
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

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
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

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
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request):
        cinemas = Cinema.objects.all().order_by('name')
        data = [{
            'id': c.id,
            'name': c.name,
            'location': c.location,
            'image': c.image.url if c.image else None
        } for c in cinemas]
        return Response({'cinemas': data}, status=status.HTTP_200_OK)

    def post(self, request):
        name = request.data.get('name')
        location = request.data.get('location')
        if not name or not location:
            return Response({'error': 'Name and location are required.'}, status=status.HTTP_400_BAD_REQUEST)
        cinema = Cinema.objects.create(name=name, location=location)
        return Response({
            'id': cinema.id,
            'name': cinema.name,
            'location': cinema.location
        }, status=status.HTTP_201_CREATED)


class CinemaDetailAPIView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request, cinema_id):
        cinema = get_object_or_404(Cinema, id=cinema_id)
        rooms = [{
            'id': r.id,
            'name': r.name
        } for r in cinema.rooms.all()]
        return Response({
            'id': cinema.id,
            'name': cinema.name,
            'location': cinema.location,
            'rooms': rooms
        }, status=status.HTTP_200_OK)

    def put(self, request, cinema_id):
        cinema = get_object_or_404(Cinema, id=cinema_id)
        cinema.name = request.data.get('name', cinema.name)
        cinema.location = request.data.get('location', cinema.location)
        cinema.save()
        return Response({
            'id': cinema.id,
            'name': cinema.name,
            'location': cinema.location
        }, status=status.HTTP_200_OK)

    def delete(self, request, cinema_id):
        cinema = get_object_or_404(Cinema, id=cinema_id)
        cinema.delete()
        return Response({'message': 'Cinema deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


# ==========================================
# SHOWTIME API
# ==========================================
class ShowtimeListAPIView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

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

    def post(self, request):
        movie_id = request.data.get('movie_id')
        room_id = request.data.get('room_id')
        start_time_str = request.data.get('start_time')
        end_time_str = request.data.get('end_time')
        base_price = request.data.get('base_price')

        if not movie_id or not room_id or not start_time_str or not end_time_str or not base_price:
            return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        movie = get_object_or_404(Movie, id=movie_id)
        room = get_object_or_404(Room, id=room_id)
        
        showtime = Showtime.objects.create(
            movie=movie,
            room=room,
            start_time=timezone.datetime.fromisoformat(start_time_str),
            end_time=timezone.datetime.fromisoformat(end_time_str),
            base_price=Decimal(str(base_price))
        )
        return Response({
            'id': showtime.id,
            'movie': showtime.movie.title,
            'room': showtime.room.name,
            'start_time': showtime.start_time.isoformat(),
            'end_time': showtime.end_time.isoformat(),
            'base_price': float(showtime.base_price)
        }, status=status.HTTP_201_CREATED)


class ShowtimeDetailAPIView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request, showtime_id):
        showtime = get_object_or_404(Showtime, id=showtime_id)
        return Response({
            'id': showtime.id,
            'movie': showtime.movie.title,
            'room': showtime.room.name,
            'cinema': showtime.room.cinema.name,
            'start_time': showtime.start_time.isoformat(),
            'end_time': showtime.end_time.isoformat(),
            'base_price': float(showtime.base_price)
        }, status=status.HTTP_200_OK)

    def put(self, request, showtime_id):
        showtime = get_object_or_404(Showtime, id=showtime_id)
        if request.data.get('movie_id'):
            showtime.movie = get_object_or_404(Movie, id=request.data.get('movie_id'))
        if request.data.get('room_id'):
            showtime.room = get_object_or_404(Room, id=request.data.get('room_id'))
        if request.data.get('start_time'):
            showtime.start_time = timezone.datetime.fromisoformat(request.data.get('start_time'))
        if request.data.get('end_time'):
            showtime.end_time = timezone.datetime.fromisoformat(request.data.get('end_time'))
        if request.data.get('base_price'):
            showtime.base_price = Decimal(str(request.data.get('base_price')))
        showtime.save()
        return Response({
            'id': showtime.id,
            'movie': showtime.movie.title,
            'start_time': showtime.start_time.isoformat(),
            'base_price': float(showtime.base_price)
        }, status=status.HTTP_200_OK)

    def delete(self, request, showtime_id):
        showtime = get_object_or_404(Showtime, id=showtime_id)
        showtime.delete()
        return Response({'message': 'Showtime deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


# Query Seat Map for specific showtime
class ShowtimeSeatsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, showtime_id):
        showtime = get_object_or_404(Showtime, id=showtime_id)
        room = showtime.room
        all_seats = Seat.objects.filter(room=room).order_by('row', 'number')
        
        booked_tickets = Ticket.objects.filter(
            booking__showtime=showtime,
            booking__status__in=['CONFIRMED', 'PENDING']
        )
        booked_seat_ids = set(ticket.seat_id for ticket in booked_tickets)
        
        seats_data = []
        for seat in all_seats:
            is_vip = seat.row in ['E', 'F', 'G']
            price = showtime.base_price * Decimal('1.20') if is_vip else showtime.base_price
            seats_data.append({
                'id': seat.id,
                'row': seat.row,
                'number': seat.number,
                'type': 'VIP' if is_vip else 'STANDARD',
                'price': float(price),
                'is_booked': seat.id in booked_seat_ids
            })
            
        return Response({
            'showtime_id': showtime.id,
            'room': room.name,
            'cinema': room.cinema.name,
            'seats': seats_data
        }, status=status.HTTP_200_OK)


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


class BookingDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        return Response(serialize_booking(booking), status=status.HTTP_200_OK)


class BookingPayAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        if booking.status != 'PENDING':
            return Response({'error': 'Chỉ có thể thanh toán các đơn hàng đang chờ (PENDING).'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            payment_obj = get_object_or_404(Payment, booking=booking)
            with transaction.atomic():
                booking.status = 'CONFIRMED'
                booking.save()
                
                payment_obj.is_successful = True
                payment_obj.transaction_id = f"LUXE-{booking.id}-{int(timezone.now().timestamp())}"
                payment_obj.paid_at = timezone.now()
                payment_obj.save()
                
            return Response({
                'message': 'Thanh toán thành công!',
                'booking': serialize_booking(booking)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
