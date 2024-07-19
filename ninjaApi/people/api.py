from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from people.models import Peoples

router = Router()

################
# MODEL SCHEMAS
################
class People(Schema):
    tmdb_id: int
    name: str
    original_name: str
    avatar_path: str
    known_for_department: int
    popularity: int

class PeopleOut(Schema):
    id: UUID
    tmdb_id: int
    name: str
    original_name: str
    avatar_path: str
    known_for_department: int
    popularity: int

################################
# API CONTROLLER METHODS
################################

# create new person
@router.post("/", auth=None)
def create_person(request, payload: People):
    person = Peoples.objects.create(**payload.dict())
    return {"id": person.id}

# get person by id
@router.get("/people/id/{id}", response=PeopleOut)
def get_person_by_id(request, id: str):
    person = get_object_or_404(Peoples, id=id)
    return person

# get person by tmdb_id
@router.get("/people/tmdb_id/{tmdb_id}", response=PeopleOut)
def get_person_by_tmdb_id(request, tmdb_id: str):
    person = get_object_or_404(Peoples, tmdb_id=tmdb_id)
    return person

# list all people
@router.get("/people/", response=List[PeopleOut])
def list_all_people(request):
    people_list = Peoples.objects.all()
    return people_list

# update person by id
@router.put("/people/id/{id}")
def update_person_by_id(request, id: str, payload: PeopleOut):
    person = get_object_or_404(Peoples, id=id)
    for attr, value in payload.dict().items():
        setattr(person, attr, value)
    person.save()
    return {"success": True}

# update person by tmdb_id
@router.put("/people/tmdb_id/{tmdb_id}")
def update_person_by_tmdb_id(request, tmdb_id: str, payload: PeopleOut):
    person = get_object_or_404(Peoples, tmdb_id=tmdb_id)
    for attr, value in payload.dict().items():
        setattr(person, attr, value)
    person.save()
    return {"success": True}

# delete/disable person by id
@router.delete("/people/id/{id}")
def delete_person_by_id(request, id: str):
    person = get_object_or_404(Peoples, id=id)
    #person.delete()
    person.enabled = False
    person.archived = True
    person.save()
    return {"success": True}

# delete/disable person by tmdb_id
@router.delete("/people/tmdb_id/{tmdb_id}")
def delete_person_by_tmdb_id(request, tmdb_id: str):
    person = get_object_or_404(Peoples, tmdb_id=tmdb_id)
    #person.delete()
    person.enabled = False
    person.archived = True
    person.save()
    return {"success": True}