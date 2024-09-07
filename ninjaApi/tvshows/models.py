import uuid
from django.db import models
from genres.models import Genres
from reviews.models import Reviews
from people.models import Peoples
from trailers.models import Trailers

class TVShows(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    tmdb_id = models.IntegerField(unique=True)
    imdb_id = models.CharField(max_length=30, unique=True, null=True, blank=True)
    poster_url = models.CharField(max_length=255, null=True, blank=True)
    backdrop_url = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255)
    rating = models.DecimalField(decimal_places=1, max_digits=4, null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    origin_location = models.CharField(max_length=50, null=True, blank=True)
    languages = models.CharField(max_length=30, null=True, blank=True)
    imdb_link = models.CharField(max_length=255, null=True, blank=True)
    youtube_trailer = models.ManyToManyField(Trailers, null=True, blank=True) # FK to trailers
    actors_cast = models.ManyToManyField(Peoples, related_name='tv_actor', null=True, blank=True) # FK to actors
    director = models.ManyToManyField(Peoples, related_name='tv_director', null=True, blank=True) # FK to actors
    genres = models.ManyToManyField(Genres, null=True, blank=True) # FK to actors
    reviews = models.ManyToManyField(Reviews, blank=True) # FK to reviews
    seasons = models.IntegerField(default=0)
    episodes = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
    expires = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)

class Episodes(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    tmdb_id = models.IntegerField(unique=True)
    tv_show_id = models.ManyToManyField(TVShows, null=True, blank=True, related_name='tv_show_id') # FK to TVShows
    tv_show_tmdb_id = models.IntegerField(null=True, blank=True)
    still_path = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255)
    rating = models.DecimalField(decimal_places=1, max_digits=4, null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    episode_number = models.IntegerField(default=0)
    runtime = models.IntegerField(default=0, null=True, blank=True)
    season_number = models.IntegerField(default=0)
    episode_type = models.CharField(max_length=50, null=True, blank=True)
    enabled = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
    expires = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)
