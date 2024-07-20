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
from decouple import config

router = Router()

################
# MODEL SCHEMAS
################
class Genre(Schema):
    tmdb_id: int
    name: str
    type: int

class GenreOut(Schema):
    id: UUID
    tmdb_id: int
    name: str
    type: int

################################
# API CONTROLLER METHODS
################################

### initial seeding ##
@router.get("/seeding/")
def genres_seeding(request):
    # genres for movies
    movie_genres_base_url = " https://api.themoviedb.org/3/genre/movie/list?language=en"

    # genres for tv shows
    tvshow_genres_base_url = " https://api.themoviedb.org/3/genre/tv/list?language=en"

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    # get movies
    movies_response = requests.get(movie_genres_base_url, headers=headers)
    movies_response_json = movies_response.json()

    if "genres" in movies_response_json:
        # get the genres
        for genre in movies_response_json['genres']:
            genre_exists = Genres.objects.filter(tmdb_id=genre['id']).first()
            if genre_exists is None:
                # create new genre in database
                new_genre = {
                    'tmdb_id': genre['id'],
                    'name': genre['name'],
                    'type': 0,
                }
                Genres.objects.create(**new_genre)

    # get tv shows
    tvshows_response = requests.get(tvshow_genres_base_url, headers=headers)
    tvshows_response_json = tvshows_response.json()

    if "genres" in tvshows_response_json:
        # get the genres
        for genre in tvshows_response_json['genres']:
            genre_exists = Genres.objects.filter(tmdb_id=genre['id']).first()
            if genre_exists is None:
                # create new genre in database
                new_genre = {
                    'tmdb_id': genre['id'],
                    'name': genre['name'],
                    'type': 1,
                }
                Genres.objects.create(**new_genre)

    return {"success": True}

### initial data loading ###
@router.get("/seeding/data")
def genres_data_loading(request):
    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    print("===== Starting movie genre data loading =====")
    movie_count = 1

    # get all movies
    movies = Movies.objects.all()
    for movie in movies:
        print(f"===== Movie #{movie_count}: {movie.title}")
        genre_list = []

        # url to get the details about a movie
        url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}?language=en-US"
        response = requests.get(url, headers=headers)
        response_json = response.json()

        # genres
        genres = response_json['genres']

        # foreach movie get the genres
        for genre in genres:
            existing_genre = Genres.objects.filter(tmdb_id=genre['id']).first()
            if existing_genre is not None:
                # check if we already have a many to many relationship with this genre for the movie
                genre_exists = movie.genres.filter(id=existing_genre.id).exists()
                if genre_exists:
                    continue # skip
                else:
                    # add genre to list to create new many to many relationship
                    genre_list.append(existing_genre)
            else:
                # create new genre
                new_genre = {
                    'tmdb_id': genre['id'],
                    'name': genre['name'],
                    'type': 0,
                }
                genre_obj = Genres.objects.create(**new_genre)
                genre_list.append(genre_obj)
        
        if len(genre_list) > 0:
            movie.genres.set(genre_list)
            movie.save()
        
        movie_count += 1

    print("===== Starting tv genre data loading =====")
    tv_count = 1

    # get all tv shows
    tvshows = TVShows.objects.all()
    for tvshow in tvshows:
        print(f"===== TV show #{tv_count}: {tvshow.title}")
        genre_list = []

        # url to get the details about a tv show
        url = f"https://api.themoviedb.org/3/tv/{tvshow.tmdb_id}?language=en-US"
        response = requests.get(url, headers=headers)
        response_json = response.json()

        # genres
        genres = response_json['genres']

        # foreach tv show get the genres
        for genre in genres:
            existing_genre = Genres.objects.filter(tmdb_id=genre['id']).first()
            if existing_genre is not None:
                # check if we already have a many to many relationship with this genre for the tv show
                genre_exists = tvshow.genres.filter(id=existing_genre.id).exists()
                if genre_exists:
                    continue # skip
                else:
                    # add genre to list to create new many to many relationship
                    genre_list.append(existing_genre)
            else:
                # create new genre
                new_genre = {
                    'tmdb_id': genre['id'],
                    'name': genre['name'],
                    'type': 1,
                }
                genre_obj = Genres.objects.create(**new_genre)
                genre_list.append(genre_obj)
        
        if len(genre_list) > 0:
            tvshow.genres.set(genre_list)
            tvshow.save()

        tv_count += 1

    return {"success": True}
    
# create new genre
@router.post("/", auth=None)
def create_genre(request, payload: Genre):
    genre = Genres.objects.create(**payload.dict())
    return {"id": genre.id}

# get genre by id
@router.get("/genres/id/{id}", response=GenreOut)
def get_genre_by_id(request, id: str):
    genre = get_object_or_404(Genres, id=id)
    return genre

# get genre by tmdb_id
@router.get("/genres/tmdb_id/{tmdb_id}", response=GenreOut)
def get_genre_by_tmdb_id(request, tmdb_id: int):
    genre = get_object_or_404(Genres, tmdb_id=tmdb_id)
    return genre

# list all genres
@router.get("/genres/", response=List[GenreOut])
def list_all_genres(request):
    genre_list = Genres.objects.all()
    return genre_list

# update genre by id
@router.put("/genres/id/{id}")
def update_genre_by_id(request, id: str, payload: GenreOut):
    genre = get_object_or_404(Genres, id=id)
    for attr, value in payload.dict().items():
        setattr(genre, attr, value)
    genre.save()
    return {"success": True}

# update genre by tmdb_id
@router.put("/genres/tmdb_id/{tmdb_id}")
def update_genre_by_tmdb_id(request, tmdb_id: int, payload: GenreOut):
    genre = get_object_or_404(Genres, tmdb_id=tmdb_id)
    for attr, value in payload.dict().items():
        setattr(genre, attr, value)
    genre.save()
    return {"success": True}

# delete/disable genre by id
@router.delete("/genres/id/{id}")
def delete_genre_by_id(request, id: str):
    genre = get_object_or_404(Genres, id=id)
    #genre.delete()
    genre.enabled = False
    genre.archived = True
    genre.save()
    return {"success": True}

# delete/disable genre by tmdb_id
@router.delete("/genres/tmdb_id/{tmdb_id}")
def delete_genre_by_tmdb_id(request, tmdb_id: int):
    genre = get_object_or_404(Genres, tmdb_id=tmdb_id)
    #genre.delete()
    genre.enabled = False
    genre.archived = True
    genre.save()
    return {"success": True}