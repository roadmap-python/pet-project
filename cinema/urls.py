from django.urls import path
from . import views

urlpatterns = [
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
    path('dashboard/', views.admin_dashboard_ui, name='dashboard'),
    path('admin-bookings/', views.admin_bookings, name='admin-bookings'),
]