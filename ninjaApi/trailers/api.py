from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
import requests
from genres.models import Genres
from movies.models import Movies
from tvshows.models import TVShows
from trailers.models import Trailers
from decouple import config

router = Router()

################
# MODEL SCHEMAS
################
class Trailer(Schema):
    name: str
    key: str
    site: str
    quality: int
    type: str
    official: bool
    published_at: datetime
    video_id: str

class TrailerOut(Schema):
    id: UUID
    name: str
    key: str
    site: str
    quality: int
    type: str
    official: bool
    published_at: datetime
    video_id: str

################################
# API CONTROLLER METHODS
################################

### initial seeding ##
@router.get("/seeding/")
def trailers_seeding(request):
    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    print("===== Trailers seeding started =====")
    movie_count = 1

    # get all movies
    movies = Movies.objects.all()
    for movie in movies:
        print(f"===== Movie #{movie_count}: {movie.title}")
        
        # trailers for movies
        movie_trailers_base_url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}/videos"

        # get movie trailers
        movies_response = requests.get(movie_trailers_base_url, headers=headers)
        movies_response_json = movies_response.json()

        for trailer in movies_response_json['results']:
            trailer_exists = Trailers.objects.filter(video_id=trailer['id']).first()
            if trailer_exists is None:
                # create new trailer in database
                new_trailer = {
                    'name': trailer['name'],
                    'key': trailer['key'],
                    'video_id': trailer['id'],
                    'site': trailer['site'],
                    'quality': trailer['size'],
                    'official': trailer['official'],
                    'published_at': trailer['published_at'],
                    'type': 0,
                }
                Trailers.objects.create(**new_trailer)
            
        movie_count += 1

    tvshow_count = 1

    # get all tv shows
    tvshows = TVShows.objects.all()
    for tvshow in tvshows:
        print(f"===== TV Show #{tvshow_count}: {tvshow.title}")

        # trailers for tv shows
        tvshow_trailers_base_url = f"https://api.themoviedb.org/3/tv/{tvshow.tmdb_id}/videos"

        # get tv shows trailers
        tvshow_response = requests.get(tvshow_trailers_base_url, headers=headers)
        tvshow_response_json = tvshow_response.json()

        for trailer in tvshow_response_json['results']:
            trailer_exists = Trailers.objects.filter(video_id=trailer['id']).first()
            if trailer_exists is None:
                # create new trailer in database
                new_trailer = {
                    'name': trailer['name'],
                    'key': trailer['key'],
                    'video_id': trailer['id'],
                    'site': trailer['site'],
                    'quality': trailer['size'],
                    'official': trailer['official'],
                    'published_at': trailer['published_at'],
                    'type': 0,
                }
                Trailers.objects.create(**new_trailer)
        
        tvshow_count += 1

    return {"success": True}

### initial data loading ###
@router.get("/seeding/data")
def trailers_data_loading(request):
    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    print("===== Starting movie trailers data loading =====")
    movie_count = 1

    # get all movies
    movies = Movies.objects.all()
    for movie in movies:
        print(f"===== Movie #{movie_count}: {movie.title}")
        trailer_list = []

        # get the trailers for a movie
        url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}/videos"
        response = requests.get(url, headers=headers)
        response_json = response.json()

        # foreach movie get the trailers
        for trailer in response_json['results']:
            existing_trailer = Trailers.objects.filter(video_id=trailer['id']).first()
            if existing_trailer is not None:
                # check if we already have a many to many relationship with this trailer for the movie
                trailer_exists = movie.youtube_trailer.filter(id=existing_trailer.id).exists()
                if trailer_exists:
                    continue # skip
                else:
                    # add trailer to list to create new many to many relationship
                    trailer_list.append(existing_trailer)
            else:
                # create a new trailer
                new_trailer = {
                    'name': trailer['name'],
                    'key': trailer['key'],
                    'site': trailer['site'],
                    'quality': trailer['size'],
                    'type': trailer['type'],
                    'official': trailer['official'],
                    'published_at': trailer['published_at'],
                    'video_id': trailer['id'],
                }
                trailer_obj = Trailers.objects.create(**new_trailer)
                trailer_list.append(trailer_obj)

        if len(trailer_list) > 0:
            movie.youtube_trailer.set(trailer_list)
            movie.save()

        movie_count += 1

    print("===== Starting tv shows trailers data loading =====")
    tvshow_count = 1

    # get all tv shows
    tvshows = TVShows.objects.all()
    for tvshow in tvshows:
        print(f"===== TV Show #{tvshow_count}: {tvshow.title}")
        trailer_list = []

        # get the trailers for a tv show
        url = f"https://api.themoviedb.org/3/tv/{tvshow.tmdb_id}/videos"
        response = requests.get(url, headers=headers)
        response_json = response.json()

        # foreach movie get the trailers
        for trailer in response_json['results']:
            existing_trailer = Trailers.objects.filter(video_id=trailer['id']).first()
            if existing_trailer is not None:
                # check if we already have a many to many relationship with this trailer for the movie
                trailer_exists = movie.youtube_trailer.filter(id=existing_trailer.id).exists()
                if trailer_exists:
                    continue # skip
                else:
                    # add trailer to list to create new many to many relationship
                    trailer_list.append(existing_trailer)
            else:
                # create a new trailer
                new_trailer = {
                    'name': trailer['name'],
                    'key': trailer['key'],
                    'site': trailer['site'],
                    'quality': trailer['size'],
                    'type': trailer['type'],
                    'official': trailer['official'],
                    'published_at': trailer['published_at'],
                    'video_id': trailer['id'],
                }
                trailer_obj = Trailers.objects.create(**new_trailer)
                trailer_list.append(trailer_obj)

        if len(trailer_list) > 0:
            movie.youtube_trailer.set(trailer_list)
            movie.save()

        tvshow_count += 1

    return {"success": True}

# create new trailer
@router.post("/", auth=None)
def create_trailer(request, payload: Trailer):
    trailer = Genres.objects.create(**payload.dict())
    return {"id": trailer.id}

# get trailer by id
@router.get("/trailers/id/{id}", response=TrailerOut)
def get_trailer_by_id(request, id: str):
    trailer = get_object_or_404(Trailers, id=id)
    return trailer

# get trailer by tmdb_id
@router.get("/trailers/tmdb_id/{tmdb_id}", response=TrailerOut)
def get_trailer_by_tmdb_id(request, tmdb_id: int):
    trailer = get_object_or_404(Trailers, tmdb_id=tmdb_id)
    return trailer

# list all trailers
@router.get("/trailers/", response=List[TrailerOut])
def list_all_trailers(request):
    trailer_list = Trailers.objects.all()
    return trailer_list

# update trailer by id
@router.put("/trailers/id/{id}")
def update_trailer_by_id(request, id: str, payload: TrailerOut):
    trailer = get_object_or_404(Trailers, id=id)
    for attr, value in payload.dict().items():
        setattr(trailer, attr, value)
    trailer.save()
    return {"success": True}

# update trailer by tmdb_id
@router.put("/trailers/tmdb_id/{tmdb_id}")
def update_trailer_by_tmdb_id(request, tmdb_id: int, payload: TrailerOut):
    trailer = get_object_or_404(Trailers, tmdb_id=tmdb_id)
    for attr, value in payload.dict().items():
        setattr(trailer, attr, value)
    trailer.save()
    return {"success": True}

# delete/disable trailer by id
@router.delete("/trailers/id/{id}")
def delete_trailer_by_id(request, id: str):
    trailer = get_object_or_404(Trailers, id=id)
    #trailer.delete()
    trailer.enabled = False
    trailer.archived = True
    trailer.save()
    return {"success": True}

# delete/disable trailer by tmdb_id
@router.delete("/trailers/tmdb_id/{tmdb_id}")
def delete_trailer_by_tmdb_id(request, tmdb_id: int):
    trailer = get_object_or_404(Trailers, tmdb_id=tmdb_id)
    #trailer.delete()
    trailer.enabled = False
    trailer.archived = True
    trailer.save()
    return {"success": True}