from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from genres.api import Genre
from people.api import People
from trailers.api import Trailer
from tvshows.models import TVShows

router = Router()

################
# MODEL SCHEMAS
################
class TVShow(Schema):
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
    seasons: int
    enabled: bool
    expires: datetime

class TVShowOut(Schema):
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
    seasons: int
    enabled: bool
    expires: datetime

################################
# API CONTROLLER METHODS
################################

# create new tv show
@router.post("/", auth=None)
def create_tv_show(request, payload: TVShow):
    tv_show = TVShows.objects.create(**payload.dict())
    return {"id": tv_show.id}

# get tv show by id
@router.get("/tv/id/{id}", response=TVShowOut)
def get_tv_show_by_id(request, id: str):
    tv_show = get_object_or_404(TVShows, id=id)
    return tv_show

# get tv show by tmdb_id
@router.get("/tv/tmdb_id/{tmdb_id}", response=TVShowOut)
def get_tv_by_tmdb_id(request, tmdb_id: int):
    tv_show = get_object_or_404(TVShows, tmdb_id=tmdb_id)
    return tv_show

# get tv show by imdb_id
@router.get("/tv/imdb_id/{imdb_id}", response=TVShowOut)
def get_tv_show_by_imdb_id(request, imdb_id: str):
    tv_show = get_object_or_404(TVShows, imdb_id=imdb_id)
    return tv_show

# list all tv shows
@router.get("/tv/", response=List[TVShowOut])
def list_all_tv_shows(request):
    tv_show_list = TVShows.objects.all()
    return tv_show_list

# update tv show by id
@router.put("/tv/id/{id}")
def update_tv_show_by_id(request, id: str, payload: TVShowOut):
    tv_show = get_object_or_404(TVShows, id=id)
    for attr, value in payload.dict().items():
        setattr(tv_show, attr, value)
    tv_show.save()
    return {"success": True}

# update tv show by tmdb_id
@router.put("/tv/tmdb_id/{tmdb_id}")
def update_tv_show_by_tmdb_id(request, tmdb_id: int, payload: TVShowOut):
    tv_show = get_object_or_404(TVShows, tmdb_id=tmdb_id)
    for attr, value in payload.dict().items():
        setattr(tv_show, attr, value)
    tv_show.save()
    return {"success": True}

# update tv show by imdb_id
@router.put("/tv/imdb_id/{imdb_id}")
def update_tv_show_by_imdb_id(request, imdb_id: str, payload: TVShowOut):
    tv_show = get_object_or_404(TVShows, imdb_id=imdb_id)
    for attr, value in payload.dict().items():
        setattr(tv_show, attr, value)
    tv_show.save()
    return {"success": True}

# delete/disable movie by id
@router.delete("/tv/id/{id}")
def delete_tv_show_by_id(request, id: str):
    tv_show = get_object_or_404(TVShows, id=id)
    #tv_show.delete()
    tv_show.enabled = False
    tv_show.archived = True
    tv_show.save()
    return {"success": True}

# delete/disable tv show by tmdb_id
@router.delete("/tv/tmdb_id/{tmdb_id}")
def delete_tv_show_by_tmdb_id(request, tmdb_id: int):
    tv_show = get_object_or_404(TVShows, tmdb_id=tmdb_id)
    #tv_show.delete()
    tv_show.enabled = False
    tv_show.archived = True
    tv_show.save()
    return {"success": True}

# delete/disable tv show by imdb_id
@router.delete("/tv/imdb_id/{imdb_id}")
def delete_tv_show_by_imdb_id(request, imdb_id: str):
    tv_show = get_object_or_404(TVShows, imdb_id=imdb_id)
    #tv_show.delete()
    tv_show.enabled = False
    tv_show.archived = True
    tv_show.save()
    return {"success": True}