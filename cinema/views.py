from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import Movie

# Create your views here.
def health(request):
    return HttpResponse("health")

def hello_world(request):
    template = loader.get_template('myfirst.html')
    return HttpResponse(template.render())

def movie_list_ui(request):
    movies = Movie.objects.all()
    # Truyền biến 'movies' vào file HTML
    return render(request, 'user_movies.html', {'movies': movies})