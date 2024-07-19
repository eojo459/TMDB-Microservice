from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from genres.models import Genres
from tvshows.models import TVShows

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