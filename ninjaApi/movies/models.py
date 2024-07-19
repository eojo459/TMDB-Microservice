import uuid
from django.db import models
from genres.models import Genres
from people.models import Peoples
from trailers.models import Trailers

class Movies(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    tmdb_id = models.IntegerField(unique=True)
    imdb_id = models.CharField(max_length=30, unique=True)
    poster_url = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    rating = models.IntegerField(default=0)
    release_date = models.DateField()
    description = models.CharField(max_length=255)
    origin_location = models.CharField(max_length=50)
    languages = models.CharField(max_length=30)
    imdb_link = models.CharField(max_length=255)
    youtube_trailer = models.ManyToManyField(Trailers) # FK to trailers
    actors_cast = models.ManyToManyField(Peoples, related_name='movie_actors') # FK to actors
    director = models.ManyToManyField(Peoples, related_name='movie_director') # FK to actors
    genres = models.ManyToManyField(Genres) # FK to actors
    run_time = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
    expires = models.DateTimeField(null=True, blank=True)
