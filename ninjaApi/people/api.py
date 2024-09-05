from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
import requests
from backendApi.utils.helper import calculate_day_difference
from movies.models import Movies
from tvshows.models import TVShows
from people.models import Peoples
from decouple import config

router = Router()

################
# MODEL SCHEMAS
################
class People(Schema):
    tmdb_id: int
    name: str
    original_name: str
    avatar_path: str | None = None
    known_for_department: str = None
    popularity: int

class PeopleOut(Schema):
    id: UUID
    tmdb_id: int
    name: str
    original_name: str
    avatar_path: str | None = None
    known_for_department: str = None
    popularity: int

################################
# API CONTROLLER METHODS
################################

### initial seeding ##
@router.get("/seeding/")
def people_seeding(request):
    skip_round_1 = False
    skip_round_2 = True

    page = 1
    max_pages = 500 # TMDB limits us to 500 pages

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    print("===== People seeding started =====")

    # 1st round get based on most popular sort by descending (highest popularity to least popularity) 
    if skip_round_1 is False:
        print("===== Starting round 1 =====")
        url = f"https://api.themoviedb.org/3/person/popular?language=en-US&page={page}"

        response = requests.get(url, headers=headers)
        response_json = response.json()

        if response_json['total_pages'] >= 1:
            # get all the pages we can get
            while page <= max_pages:
                print("===== Page " + str(page) + " =====")

                # for each result on this page, create new person entry in database if doesn't already exist
                for result in response_json['results']:
                    person_info = {
                        'tmdb_id': result['id'],
                        'name': result['name'],
                        'original_name': result['original_name'],
                        'avatar_path': result['profile_path'],
                        'known_for_department': result['known_for_department'],
                        'popularity': result['popularity'],
                    }

                    # check if person doesn't already exist
                    person_exists = Peoples.objects.filter(tmdb_id=result['id']).first()
                    if person_exists and person_exists.last_updated is not None:
                        if calculate_day_difference(person_exists.last_updated.strftime('%Y-%m-%d'), 7):
                            # update person entry
                            person_exists.tmdb_id = result['id']
                            person_exists.avatar_path = result['profile_path']
                            person_exists.name = result['name']
                            person_exists.original_name = result['original_name']
                            person_exists.known_for_department = result['known_for_department']
                            person_exists.popularity = result['popularity']
                            person_exists.last_updated = datetime.now().date()
                            person_exists.save()
                    elif person_exists is None:
                        # create new person entry
                        Peoples.objects.create(**person_info)
                    else:
                        continue # skip

                # go to next page
                page += 1
                url = f"https://api.themoviedb.org/3/person/popular?language=en-US&page={page}"
                response = requests.get(url, headers=headers)
                response_json = response.json()

        print("===== End of round 1 =====")

    # 2nd round get based on trending sort by descending (most trending to least trending) 
    if skip_round_2 is False:
        page = 1
        trending_type = "week" # day or week
        url = f"https://api.themoviedb.org/3/trending/person/{trending_type}?language=en-US&page={page}"

        response = requests.get(url, headers=headers)
        response_json = response.json()

        if response_json['total_pages'] >= 1:
            print("===== Starting round 2 =====")
            # get all the pages we can get
            while page <= max_pages:
                print("===== Page " + str(page) + " =====")

                # for each result on this page, create new movie entry in database if doesn't already exist
                for result in response_json['results']:
                    person_info = {
                        'tmdb_id': result['id'],
                        'name': result['name'],
                        'original_name': result['original_name'],
                        'avatar_path': result['profile_path'],
                        'known_for_department': result['known_for_department'],
                        'popularity': result['popularity'],
                    }

                    # check if person doesn't already exist
                    person_exists = Peoples.objects.filter(tmdb_id=result['id']).first()
                    if person_exists and person_exists.last_updated is not None:
                        if calculate_day_difference(person_exists.last_updated.strftime('%Y-%m-%d'), 7):
                            # update person entry
                            person_exists.tmdb_id = result['id']
                            person_exists.avatar_path = result['profile_path']
                            person_exists.name = result['name']
                            person_exists.original_name = result['original_name']
                            person_exists.known_for_department = result['known_for_department']
                            person_exists.popularity = result['popularity']
                            person_exists.last_updated = datetime.now().date()
                            person_exists.save()
                    elif person_exists is None:
                        # create new person entry
                        Peoples.objects.create(**person_info)
                    else:
                        continue # skip

                # go to next page
                page += 1
                url = f"https://api.themoviedb.org/3/trending/person/{trending_type}?language=en-US&page={page}"
                response = requests.get(url, headers=headers)
                response_json = response.json()
    
    return {"success": True}

### initial data loading ###
@router.get("/seeding/data")
def people_data_loading(request):
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
        actor_list = []
        director_list = []

        # url to get the details about a movie
        url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}?language=en-US&append_to_response=credits"
        response = requests.get(url, headers=headers)
        response_json = response.json()

        # people credits
        credits = response_json['credits']

        # foreach movie get the credits then actors and directors
        for result in credits['cast']:
            existing_person = Peoples.objects.filter(tmdb_id=result['id']).first()
            if existing_person is not None:
                # check if we already have a many to many relationship with this person for the movie
                actor_exists = movie.actors_cast.filter(id=existing_person.id).exists()
                if actor_exists:
                    continue # skip
                else:
                    # add actor to list to create new many to many relationship
                    if result['known_for_department'] == 'Acting':
                        if 'job' in result and result['job'] == 'Director':
                            director_list.append(existing_person)
                        else:
                            actor_list.append(existing_person)
            else:
                if result['known_for_department'] == 'Acting':
                    if 'job' in result and result['job'] == 'Director':
                        # create new people entry for director
                        new_person = {
                            'tmdb_id': result['id'],
                            'name': result['name'],
                            'original_name': result['original_name'],
                            'avatar_path': result['profile_path'],
                            'known_for_department': result['job'],
                            'popularity': result['popularity'],
                        }
                        person = Peoples.objects.create(**new_person)
                        director_list.append(person)
                    else:
                        # create new people entry for actor
                        new_person = {
                            'tmdb_id': result['id'],
                            'name': result['name'],
                            'original_name': result['original_name'],
                            'avatar_path': result['profile_path'],
                            'known_for_department': result['known_for_department'],
                            'popularity': result['popularity'],
                        }
                        person = Peoples.objects.create(**new_person)
                        actor_list.append(person)

        if len(actor_list) > 0:
            movie.actors_cast.set(actor_list)
            movie.save()
        
        if len(director_list) > 0:
            movie.director.set(director_list)
            movie.save()

        movie_count += 1

    print("===== Starting tv show genre data loading =====")
    tvshow_count = 1

    # get all tv shows
    tvshows = TVShows.objects.all()
    for tvshow in tvshows:
        print(f"===== Tv show #{tvshow_count}: {tvshow.title}")
        actor_list = []
        director_list = []

        # url to get the details about a tv show
        url = f"https://api.themoviedb.org/3/tv/{tvshow.tmdb_id}?language=en-US&append_to_response=credits"
        response = requests.get(url, headers=headers)
        response_json = response.json()

        # people credits
        credits = response_json['credits']

        # foreach movie get the credits then actors and directors
        for result in credits['cast']:
            existing_person = Peoples.objects.filter(tmdb_id=result['id']).first()
            if existing_person is not None:
                # check if we already have a many to many relationship with this person for the tv show
                actor_exists = movie.actors_cast.filter(id=existing_person.id).exists()
                if actor_exists:
                    continue # skip
                else:
                    # add actor to list to create new many to many relationship
                    if result['known_for_department'] == 'Acting':
                        if 'job' in result and result['job'] == 'Director':
                            director_list.append(existing_person)
                        else:
                            actor_list.append(existing_person)
            else:
                if result['known_for_department'] == 'Acting':
                    if 'job' in result and result['job'] == 'Director':
                        # create new people entry for director
                        new_person = {
                            'tmdb_id': result['id'],
                            'name': result['name'],
                            'original_name': result['original_name'],
                            'avatar_path': result['profile_path'],
                            'known_for_department': result['job'],
                            'popularity': result['popularity'],
                        }
                        person = Peoples.objects.create(**new_person)
                        director_list.append(person)
                    else:
                        # create new people entry for actor
                        new_person = {
                            'tmdb_id': result['id'],
                            'name': result['name'],
                            'original_name': result['original_name'],
                            'avatar_path': result['profile_path'],
                            'known_for_department': result['known_for_department'],
                            'popularity': result['popularity'],
                        }
                        person = Peoples.objects.create(**new_person)
                        actor_list.append(person)

        if len(actor_list) > 0:
            tvshow.actors_cast.set(actor_list)
            tvshow.save()
        
        if len(director_list) > 0:
            tvshow.director.set(director_list)
            tvshow.save()

        tvshow_count += 1

    return {"success": True}

# create new person
@router.post("/", auth=None)
def create_person(request, payload: People):
    person = Peoples.objects.create(**payload.dict())
    return {"id": person.id}

# get person by id
@router.get("/id/{id}", response=PeopleOut)
def get_person_by_id(request, id: str):
    person = get_object_or_404(Peoples, id=id)
    return person

# get person by tmdb_id
@router.get("/tmdb_id/{tmdb_id}", response=PeopleOut)
def get_person_by_tmdb_id(request, tmdb_id: str):
    person = get_object_or_404(Peoples, tmdb_id=tmdb_id)
    return person

# list all people
@router.get("/", response=List[PeopleOut])
def list_all_people(request):
    people_list = Peoples.objects.all()
    return people_list

# update person by id
@router.put("/id/{id}")
def update_person_by_id(request, id: str, payload: PeopleOut):
    person = get_object_or_404(Peoples, id=id)
    for attr, value in payload.dict().items():
        setattr(person, attr, value)
    person.save()
    return {"success": True}

# update person by tmdb_id
@router.put("/tmdb_id/{tmdb_id}")
def update_person_by_tmdb_id(request, tmdb_id: str, payload: PeopleOut):
    person = get_object_or_404(Peoples, tmdb_id=tmdb_id)
    for attr, value in payload.dict().items():
        setattr(person, attr, value)
    person.save()
    return {"success": True}

# delete/disable person by id
@router.delete("/id/{id}")
def delete_person_by_id(request, id: str):
    person = get_object_or_404(Peoples, id=id)
    #person.delete()
    person.enabled = False
    person.archived = True
    person.save()
    return {"success": True}

# delete/disable person by tmdb_id
@router.delete("/tmdb_id/{tmdb_id}")
def delete_person_by_tmdb_id(request, tmdb_id: str):
    person = get_object_or_404(Peoples, tmdb_id=tmdb_id)
    #person.delete()
    person.enabled = False
    person.archived = True
    person.save()
    return {"success": True}