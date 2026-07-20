from django.contrib import admin
from .models import Genre, Movie, Cinema, Room, Seat, Showtime, Booking, Ticket, Payment

# Register your models here.
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration', 'rating')
    search_fields = ('title', 'actors', 'description')
    list_filter = ('genres',)

@admin.register(Cinema)
class CinemaAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    search_fields = ('name', 'location')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'cinema')
    list_filter = ('cinema',)

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('room', 'row', 'number')
    list_filter = ('room__cinema', 'room')

@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ('movie', 'room', 'start_time', 'end_time', 'base_price')
    list_filter = ('room__cinema', 'movie', 'start_time')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'showtime', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'id')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('booking', 'seat')
    search_fields = ('booking__id', 'seat__row', 'seat__number')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'transaction_id', 'is_successful', 'paid_at')
    list_filter = ('is_successful', 'paid_at')
    search_fields = ('transaction_id', 'booking__id')