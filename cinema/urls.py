from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.urls import path
from . import views
from . import api_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # RESTful APIs
    path('api/auth/register/', api_views.RegisterAPIView.as_view(), name='api-register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='api-login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='api-refresh'),

    path('api/movies/', api_views.MovieListAPIView.as_view(), name='api-movie-list'),
    path('api/movies/<int:movie_id>/', api_views.MovieDetailAPIView.as_view(), name='api-movie-detail'),
    path('api/cinemas/', api_views.CinemaListAPIView.as_view(), name='api-cinema-list'),
    path('api/showtimes/', api_views.ShowtimeListAPIView.as_view(), name='api-showtime-list'),
    path('api/bookings/', api_views.BookingAPIView.as_view(), name='api-booking-list'),

    path('health/', views.health, name='health'),
    path('', views.index, name='home'),

    # Authenticate
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    path('forgot-password/', views.user_forgot_password, name='forgot-password'),

    # Movie details and booking flow
    path('movies/', views.movie_list_ui, name='movie-list'),
    path('movies/<int:movie_id>/', views.movie_detail_ui, name='movie-detail'),
    path('booking/select-cinema/<int:movie_id>/', views.select_cinema, name='select-cinema'),
    path('booking/select-showtime/<int:movie_id>/<int:cinema_id>/', views.select_showtime, name='select-showtime'),
    path('booking/select-seats/<int:showtime_id>/', views.select_seats, name='select-seats'),
    path('booking/payment/<int:booking_id>/', views.payment, name='payment'),
    path('booking/success/<int:booking_id>/', views.booking_success, name='booking-success'),
    
    path('my-bookings/', views.my_bookings, name='my-bookings'),

    # Admin page
    path('manage/dashboard/', views.admin_dashboard_ui, name='dashboard'),
    path('manage/bookings/', views.admin_bookings, name='admin-bookings'),
    
    # Movie CRUD
    path('manage/movies/', views.admin_movies, name='admin-movies'),
    path('manage/movies/create/', views.admin_movie_create, name='admin-movie-create'),
    path('manage/movies/edit/<int:movie_id>/', views.admin_movie_edit, name='admin-movie-edit'),
    path('manage/movies/delete/<int:movie_id>/', views.admin_movie_delete, name='admin-movie-delete'),
    
    # Cinema CRUD
    path('manage/cinemas/', views.admin_cinemas, name='admin-cinemas'),
    path('manage/cinemas/create/', views.admin_cinema_create, name='admin-cinema-create'),
    path('manage/cinemas/edit/<int:cinema_id>/', views.admin_cinema_edit, name='admin-cinema-edit'),
    path('manage/cinemas/delete/<int:cinema_id>/', views.admin_cinema_delete, name='admin-cinema-delete'),
    
    # Showtime CRUD
    path('manage/showtimes/', views.admin_showtimes, name='admin-showtimes'),
    path('manage/showtimes/create/', views.admin_showtime_create, name='admin-showtime-create'),
    path('manage/showtimes/edit/<int:showtime_id>/', views.admin_showtime_edit, name='admin-showtime-edit'),
    path('manage/showtimes/delete/<int:showtime_id>/', views.admin_showtime_delete, name='admin-showtime-delete'),
]