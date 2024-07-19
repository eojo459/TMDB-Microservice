from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from movies.models import Movies
from genres.api import Genre
from people.api import People
from trailers.api import Trailer

router = Router()

################
# MODEL SCHEMAS
################
class Movie(Schema):
    tmdb_id: int
    imdb_id: str
    poster_url: str
    title: str
    rating: int
    release_date: date
    description: str
    origin_location: str
    languages: str
    imdb_link: str
    youtube_trailer: List[Trailer]
    actors_cast: List[People]
    director: List[People]
    genres: List[Genre]
    run_time: int
    enabled: bool
    expires: datetime

class MovieOut(Schema):
    id: UUID
    tmdb_id: int
    imdb_id: str
    poster_url: str
    title: str
    rating: int
    release_date: date
    description: str
    origin_location: str
    languages: str
    imdb_link: str
    youtube_trailer: List[Trailer]
    actors_cast: List[People]
    director: List[People]
    genres: List[Genre]
    run_time: int
    enabled: bool
    expires: datetime

################################
# API CONTROLLER METHODS
################################

# create new movie
@router.post("/", auth=None)
def create_movie(request, payload: Movie):
    movie = Movies.objects.create(**payload.dict())
    return {"id": movie.id}

# get movie by id
@router.get("/movies/id/{id}", response=MovieOut)
def get_movie_by_id(request, id: str):
    movie = get_object_or_404(Movies, id=id)
    return movie

# get movie by tmdb_id
@router.get("/movies/tmdb_id/{tmdb_id}", response=MovieOut)
def get_movie_by_tmdb_id(request, tmdb_id: int):
    movie = get_object_or_404(Movies, tmdb_id=tmdb_id)
    return movie

# get movie by imdb_id
@router.get("/movies/imdb_id/{imdb_id}", response=MovieOut)
def get_movie_by_imdb_id(request, imdb_id: str):
    movie = get_object_or_404(Movies, imdb_id=imdb_id)
    return movie

# list all movies
@router.get("/movies/", response=List[MovieOut])
def list_all_movies(request):
    movies_list = Movies.objects.all()
    return movies_list

# update movie by id
@router.put("/movies/id/{id}")
def update_movie_by_id(request, id: str, payload: MovieOut):
    movie = get_object_or_404(Movies, id=id)
    for attr, value in payload.dict().items():
        setattr(movie, attr, value)
    movie.save()
    return {"success": True}

# update movie by tmdb_id
@router.put("/movies/tmdb_id/{tmdb_id}")
def update_movie_by_tmdb_id(request, tmdb_id: int, payload: MovieOut):
    movie = get_object_or_404(Movies, tmdb_id=tmdb_id)
    for attr, value in payload.dict().items():
        setattr(movie, attr, value)
    movie.save()
    return {"success": True}

# update movie by imdb_id
@router.put("/movies/imdb_id/{imdb_id}")
def update_movie_by_imdb_id(request, imdb_id: str, payload: MovieOut):
    movie = get_object_or_404(Movies, imdb_id=imdb_id)
    for attr, value in payload.dict().items():
        setattr(movie, attr, value)
    movie.save()
    return {"success": True}

# delete/disable movie by id
@router.delete("/movies/id/{id}")
def delete_movie_by_id(request, id: str):
    movie = get_object_or_404(Movies, id=id)
    #movie.delete()
    movie.enabled = False
    movie.archived = True
    movie.save()
    return {"success": True}

# delete/disable movie by tmdb_id
@router.delete("/movies/tmdb_id/{tmdb_id}")
def delete_movie_by_tmdb_id(request, tmdb_id: int):
    movie = get_object_or_404(Movies, tmdb_id=tmdb_id)
    #movie.delete()
    movie.enabled = False
    movie.archived = True
    movie.save()
    return {"success": True}

# delete/disable movie by imdb_id
@router.delete("/movies/imdb_id/{imdb_id}")
def delete_movie_by_imdb_id(request, imdb_id: str):
    movie = get_object_or_404(Movies, imdb_id=imdb_id)
    #movie.delete()
    movie.enabled = False
    movie.archived = True
    movie.save()
    return {"success": True}