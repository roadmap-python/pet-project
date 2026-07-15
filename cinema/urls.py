from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('hello/', views.hello_world, name='hello_world'),
    path('movies/', views.movie_list_ui, name='ui-moviews-list')
]