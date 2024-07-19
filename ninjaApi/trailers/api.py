from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from genres.models import Genres
from trailers.models import Trailers

router = Router()

################
# MODEL SCHEMAS
################
class Trailer(Schema):
    tmdb_id: int
    name: str
    key: str
    site: str
    quality: int
    type: int
    official: bool
    published_at: datetime
    video_id: int

class TrailerOut(Schema):
    id: UUID
    tmdb_id: int
    name: str
    key: str
    site: str
    quality: int
    type: int
    official: bool
    published_at: datetime
    video_id: int

################################
# API CONTROLLER METHODS
################################

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