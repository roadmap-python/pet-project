
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework import status
from django.urls import reverse
from rest_framework.test import APITestCase
from cinema.models import *

class AuthAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse('api-register')
        self.login_url = reverse('api-login')

    def test_register_user_success(self):
        payload = {
            'full_name': 'Nguyen Van A',
            'phone_number': '0912345678',
            'email': 'user_a@example.com',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }

        response = self.client.post(self.register_url, payload, format='json')

        # Expect
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])

    def test_register_duplicate_email_fails(self):
        User.objects.create_user(username="user_a@example.com", email="user_a@example.com", password="Password123")
        payload = {
            'full_name': 'Nguyen Van A',
            'phone_number': '0912345678',
            'email': 'user_a@example.com',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }

        response = self.client.post(self.register_url, payload, format='json')

        # Expect 
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_user_success(self):
        user = User.objects.create_user(username="user_a@example.com", email="user_a@example.com", password="Password123")
        payload = {
            'username': 'user_a@example.com',
            'password': 'Password123'
        }

        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_password_wrong_fails(self):
        User.objects.create_user(username="user_a@example.com", email="user_a@example.com", password="Password123")
        payload = {
            'username': 'user_a@example.com',
            'password': 'Password1234'
        }

        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class MovieAPITests(APITestCase):
    def setUp(self):
        self.movie1 = Movie.objects.create(
            title='Inception',
            duration=148,
            description='Mind-bending thriller',
            rating=Decimal('8.8')
        )

    def test_get_movie_list(self):
        url = reverse('api-movie-list')
        response = self.client.get(url)

        # Expect
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('movies', response.data)
        self.assertEqual(len(response.data['movies']), 1)

    def test_get_movie_detail(self):
        url = reverse('api-movie-detail', kwargs={
            'movie_id': self.movie1.id
        })

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Inception')

    def test_create_movie_as_admin_success(self):
        admin = User.objects.create_superuser(username='admin@example.com', email='admin@example.com', password='password')
        self.client.force_authenticate(user=admin)
        url = reverse('api-movie-list')
        payload = {
            'title': 'Avatar 2',
            'duration': 192,
            'description': 'Sci-fi blockbuster',
            'rating': 7.8
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Avatar 2')

    def test_create_movie_as_normal_user_forbidden(self):
        user = User.objects.create_user(username='normal@example.com', email='normal@example.com', password='password')
        self.client.force_authenticate(user=user)
        url = reverse('api-movie-list')
        payload = {'title': 'Avatar 2', 'duration': 192}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class CinemaAndShowtimeAPITests(APITestCase):
    def setUp(self):
        self.cinema = Cinema.objects.create(name='Luxe Cinema Center', location='Ha Noi')
        self.room = Room.objects.create(cinema=self.cinema, name='Hall 1')
        self.seat_a1 = Seat.objects.create(room=self.room, row='A', number=1)
        self.seat_e1 = Seat.objects.create(room=self.room, row='E', number=1)

        self.movie = Movie.objects.create(title='Interstellar', duration=169, rating=Decimal('8.6'))
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            room=self.room,
            start_time=timezone.now() + timezone.timedelta(days=1),
            end_time=timezone.now() + timezone.timedelta(days=1, hours=3),
            base_price=Decimal('100000.00')
        )

    def test_get_cinemas(self):
        url = reverse('api-cinema-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['cinemas']), 1)

    def test_get_showtimes(self):
        url = reverse('api-showtime-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['showtimes']), 1)

    def test_get_showtime_seats(self):
        url = reverse('api-showtime-seats', kwargs={'showtime_id': self.showtime.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('seats', response.data)
        self.assertEqual(len(response.data['seats']), 2)

class BookingAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='customer@example.com', email='customer@example.com', password='Password123')
        
        self.cinema = Cinema.objects.create(name='Luxe Cinema Landmark', location='HCM')
        self.room = Room.objects.create(cinema=self.cinema, name='VIP Room 1')
        self.seat_1 = Seat.objects.create(room=self.room, row='A', number=1)
        
        self.movie = Movie.objects.create(title='Oppenheimer', duration=180, rating=Decimal('8.9'))
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            room=self.room,
            start_time=timezone.now() + timezone.timedelta(days=1),
            end_time=timezone.now() + timezone.timedelta(days=1, hours=3),
            base_price=Decimal('120000.00')
        )

    def test_create_booking_unauthenticated_fails(self):
        url = reverse('api-booking-list')
        payload = {
            'showtime_id': self.showtime.id,
            'selected_seat_ids': [self.seat_1.id]
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_and_pay_booking_success(self):
        # Authenticate user
        self.client.force_authenticate(user=self.user)
        
        # 1. Create Booking
        booking_url = reverse('api-booking-list')
        payload = {
            'showtime_id': self.showtime.id,
            'selected_seat_ids': [self.seat_1.id]
        }
        response = self.client.post(booking_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking_id = response.data['id']
        self.assertEqual(response.data['status'], 'PENDING')

        # 2. Pay Booking
        pay_url = reverse('api-booking-pay', kwargs={'booking_id': booking_id})
        pay_response = self.client.post(pay_url)
        self.assertEqual(pay_response.status_code, status.HTTP_200_OK)
        self.assertEqual(pay_response.data['booking']['status'], 'CONFIRMED')