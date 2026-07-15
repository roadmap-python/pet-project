from django.contrib import admin
from .models import Genre, Movie, Cinema, Room, Seat, Showtime, Booking, Ticket, Payment

# Register your models here.
admin.site.register(Genre)
admin.site.register(Movie)
admin.site.register(Cinema)
admin.site.register(Room)
admin.site.register(Seat)
admin.site.register(Booking)
admin.site.register(Showtime)
admin.site.register(Ticket)
admin.site.register(Payment)