from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
import requests
from genres.api import Genre
from backendApi.utils.helper import calculate_day_difference
from genres.models import Genres
from people.models import Peoples
from trailers.models import Trailers
from people.api import People
from trailers.api import Trailer
from tvshows.models import TVShows
from decouple import config

router = Router()

################
# MODEL SCHEMAS
################
class TVShow(Schema):
    tmdb_id: int
    imdb_id: str
    poster_url: str | None = None
    title: str
    rating: float | None = None
    release_date: date
    description: str
    origin_location: str | None = None
    languages: str
    imdb_link: str
    youtube_trailer: List[Trailer]
    actors_cast: List[People]
    director: List[People]
    genres: List[Genre]
    seasons: int
    enabled: bool
    expires: datetime | None = None

class TVShowRecommendations(Schema):
    tmdb_id: int
    imdb_id: str | None = None
    poster_url: str | None = None
    title: str
    rating: float
    release_date: date
    description: str
    genres: List[int] | None = None
    languages: str
    media_type: str
    #run_time: int

class TVShowOut(Schema):
    id: UUID
    tmdb_id: int
    imdb_id: str
    poster_url: str | None = None
    title: str
    rating: float | None = None
    release_date: date
    description: str
    origin_location: str | None = None
    languages: str
    imdb_link: str
    youtube_trailer: List[Trailer]
    actors_cast: List[People]
    director: List[People]
    genres: List[Genre]
    recommendations: List[TVShowRecommendations] | None = None
    seasons: int
    enabled: bool
    expires: datetime | None = None

################################
# API CONTROLLER METHODS
################################

### initial seeding ##
@router.get("/seeding/")
def tvshows_seeding(request):
    skip_round_1 = False
    skip_round_2 = True

    # TODO fetch data from other sources too
    fetch_new_tvshows_TMDB(skip_round_1, skip_round_2)
    return {"success": True}
   #return response.json()

### initial data loading ##
@router.get("/seeding/data")
def tvshows_data_loading(request):
    # TODO load data from other sources too
    load_tv_data_TMDB()
    return {"success": True}

# create new tv show
@router.post("/", auth=None)
def create_tv_show(request, payload: TVShow):
    tv_show = TVShows.objects.create(**payload.dict())
    return {"id": tv_show.id}

# get tv show by id
@router.get("/id/{id}", response=TVShowOut)
def get_tv_show_by_id(request, id: str):
    tv_show = get_object_or_404(TVShows, id=id)
    tv_show.recommendations = get_tv_recommendations_logic_TMDB(id)
    return tv_show

# get tv show by tmdb_id
@router.get("/tmdb_id/{tmdb_id}", response=TVShowOut)
def get_tv_by_tmdb_id(request, tmdb_id: int):
    tv_show = get_object_or_404(TVShows, tmdb_id=tmdb_id)
    tv_show.recommendations = get_tv_recommendations_logic_TMDB(tmdb_id)
    return tv_show

# get tv show by imdb_id
@router.get("/imdb_id/{imdb_id}", response=TVShowOut)
def get_tv_show_by_imdb_id(request, imdb_id: str):
    tv_show = get_object_or_404(TVShows, imdb_id=imdb_id)
    tv_show.recommendations = get_tv_recommendations_logic_TMDB(imdb_id)
    return tv_show

# list all tv shows
@router.get("/", response=List[TVShowOut])
def list_all_tv_shows(request):
    tv_show_list = TVShows.objects.prefetch_related(
        'youtube_trailer',
        'actors_cast',
        'director',
        'genres',
        'reviews'
    ).all()[:999]
    return tv_show_list

# list all tv show that contain a str in their title
@router.get("/title/{title_str}", response=List[TVShowOut])
def get_tvshows_by_title(request, title_str: str):
    shows_list = TVShows.objects.prefetch_related(
        'youtube_trailer',
        'actors_cast',
        'director',
        'genres',
        'reviews'
    ).filter(title__icontains=title_str)[:999]
    return shows_list

# update tv show by id
@router.put("/id/{id}")
def update_tv_show_by_id(request, id: str, payload: TVShowOut):
    tv_show = get_object_or_404(TVShows, id=id)
    for attr, value in payload.dict().items():
        setattr(tv_show, attr, value)
    tv_show.save()
    return {"success": True}

# update tv show by tmdb_id
@router.put("/tmdb_id/{tmdb_id}")
def update_tv_show_by_tmdb_id(request, tmdb_id: int, payload: TVShowOut):
    tv_show = get_object_or_404(TVShows, tmdb_id=tmdb_id)
    for attr, value in payload.dict().items():
        setattr(tv_show, attr, value)
    tv_show.save()
    return {"success": True}

# update tv show by imdb_id
@router.put("/imdb_id/{imdb_id}")
def update_tv_show_by_imdb_id(request, imdb_id: str, payload: TVShowOut):
    tv_show = get_object_or_404(TVShows, imdb_id=imdb_id)
    for attr, value in payload.dict().items():
        setattr(tv_show, attr, value)
    tv_show.save()
    return {"success": True}

# delete/disable movie by id
@router.delete("/id/{id}")
def delete_tv_show_by_id(request, id: str):
    tv_show = get_object_or_404(TVShows, id=id)
    #tv_show.delete()
    tv_show.enabled = False
    tv_show.archived = True
    tv_show.save()
    return {"success": True}

# delete/disable tv show by tmdb_id
@router.delete("/tmdb_id/{tmdb_id}")
def delete_tv_show_by_tmdb_id(request, tmdb_id: int):
    tv_show = get_object_or_404(TVShows, tmdb_id=tmdb_id)
    #tv_show.delete()
    tv_show.enabled = False
    tv_show.archived = True
    tv_show.save()
    return {"success": True}

# delete/disable tv show by imdb_id
@router.delete("/imdb_id/{imdb_id}")
def delete_tv_show_by_imdb_id(request, imdb_id: str):
    tv_show = get_object_or_404(TVShows, imdb_id=imdb_id)
    #tv_show.delete()
    tv_show.enabled = False
    tv_show.archived = True
    tv_show.save()
    return {"success": True}

# get all recommendations/similiar tv shows for a tv show
@router.get("/{tmdb_id}/recommended/", response=List[TVShowRecommendations])
def get_tv_recommendations(request, tmdb_id: str):
    # TODO: make this more robust and possibly use AI to get better recommendations

    tv_found = False

   # try tmdb id
    tv_show = TVShows.objects.filter(tmdb_id=tmdb_id).first()
    if tv_show is not None:
        tv_found = True
            
    if tv_found == False:
        return {"Message": "TV show not found"}

    return get_tv_recommendations_logic_TMDB(tmdb_id)


#################################
# HELPERS
#################################

# fetch new tv shows from TMDB
def fetch_new_tvshows_TMDB(skip_round_1=False, skip_round_2=True):
    # get tv shows
    base_url = "https://api.themoviedb.org/3/discover/tv"
    page = 1
    max_pages = 500 # TMDB limits us to 500 pages

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    # 1st round get based on most popular sort by descending (highest popularity to least popularity) 
    if skip_round_1 is False:
        print("===== Starting round 1 =====")
        url = f"{base_url}?include_adult=false&language=en-US&page={page}&sort_by=popularity.desc"

        response = requests.get(url, headers=headers)
        response_json = response.json()

        total_pages = response_json['total_pages']
        if total_pages >= 1:
            # get all the pages we can get
            while page <= max_pages:
                print("===== Page " + str(page) + " =====")

                # for each result on this page, create new tv show entry in database if doesn't already exist
                for result in response_json['results']:
                    tvshow_info = {
                        'tmdb_id': result['id'],
                        'imdb_id': "zz" + str(result['id']),
                        'poster_url': result['poster_path'],
                        'title': result['name'][:255],
                        'rating': result['vote_average'],
                        'release_date': '9999-01-01' if result['first_air_date'] == '' else result['first_air_date'],
                        'description': result['overview'][:255],
                        'origin_location': '',
                        'languages': result['original_language'],
                        'imdb_link': '',
                        'last_updated': datetime.now().date(),
                        'seasons': 0,
                    }

                    # check if tv show doesn't already exist
                    tvshow_exists = TVShows.objects.filter(tmdb_id=result['id']).first()
                    if tvshow_exists and tvshow_exists.last_updated is not None:
                        if calculate_day_difference(tvshow_exists.last_updated.strftime('%Y-%m-%d'), 7):
                            # update tv show entry
                            tvshow_exists.tmdb_id = result['id']
                            tvshow_exists.poster_url = result['poster_path']
                            tvshow_exists.title = result['name']
                            tvshow_exists.rating = result['rating']
                            tvshow_exists.release_date = result['first_air_date']
                            tvshow_exists.description = result['overview'][:255]
                            tvshow_exists.last_updated = datetime.now().date()
                            tvshow_exists.save()
                    elif tvshow_exists is None:
                        # create new tv show entry
                        TVShows.objects.create(**tvshow_info)
                    else:
                        continue # skip

                # go to next page
                page += 1
                url = f"{base_url}?include_adult=false&language=en-US&page={page}&sort_by=popularity.desc"
                response = requests.get(url, headers=headers)
                response_json = response.json()

        print("===== End of round 1 =====")

    # 2nd round get based on release date sort by descending (newest to oldest) 
    if skip_round_2 is False:
        page = 1
        release_date_min = "1970-01-01"
        release_date_max = "2025-12-31"
        url = f"{base_url}?include_adult=false&language=en-US&primary_release_date.gte={release_date_min}&primary_release_date.lte={release_date_max}&page={page}&sort_by=primary_release_date.desc"

        response = requests.get(url, headers=headers)
        response_json = response.json()

        if response_json['total_pages'] > 1:
            print("===== Starting round 2 =====")
            # get all the pages we can get
            while page <= max_pages:
                print("===== Page " + str(page) + " =====")

                # for each result on this page, create new tv show entry in database if doesn't already exist
                for result in response_json['results']:
                    tvshow_info = {
                        'tmdb_id': result['id'],
                        'imdb_id': "zz" + str(result['id']),
                        'poster_url': result['poster_path'],
                        'title': result['name'][:255],
                        'rating': result['vote_average'],
                        'release_date': '9999-01-01' if result['first_air_date'] == '' else result['first_air_date'],
                        'description': result['overview'][:255],
                        'origin_location': '',
                        'languages': result['original_language'],
                        'imdb_link': '',
                        'seasons': 0,
                        'last_updated': datetime.now().date(),
                    }

                    # check if tv show doesn't already exist
                    tvshow_exists = TVShows.objects.filter(tmdb_id=result['id']).first()
                    if tvshow_exists and tvshow_exists.last_updated is not None:
                        if calculate_day_difference(tvshow_exists.last_updated.strftime('%Y-%m-%d'), 7):
                            # update tv show entry
                            tvshow_exists.tmdb_id = result['id']
                            tvshow_exists.poster_url = result['poster_path']
                            tvshow_exists.title = result['name']
                            tvshow_exists.rating = result['rating']
                            tvshow_exists.release_date = result['first_air_date']
                            tvshow_exists.description = result['overview'][:255]
                            tvshow_exists.last_updated = datetime.now().date()
                            tvshow_exists.save()
                    elif tvshow_exists is None:
                        # create new tv show entry
                        TVShows.objects.create(**tvshow_info)
                    else:
                        continue # skip

                # go to next page
                page += 1
                url = f"{base_url}?include_adult=false&language=en-US&primary_release_date.gte={release_date_min}&primary_release_date.lte={release_date_max}&page={page}&sort_by=primary_release_date.desc"
                response = requests.get(url, headers=headers)
                response_json = response.json()

    return True


# get recommendations for the tv show specified
def get_tv_recommendations_logic_TMDB(series_id):
    recommendation_list = []

    # get movies
    base_url = f"https://api.themoviedb.org/3/tv/{series_id}/recommendations"
    page = 1
    max_pages = 10 # TMDB limits us to 500 pages

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    print(f"===== Getting recommendations for {series_id} =====")
    url = f"{base_url}?include_adult=false&language=en-US&page={page}&sort_by=popularity.desc"
    #url = f"{base_url}?include_adult=false&language=en-US&page={page}"

    response = requests.get(url, headers=headers)
    response_json = response.json()

    if response_json['total_pages'] > 1:
        # get all the pages we can get
        while page <= max_pages:
            #print("===== Page " + str(page) + " =====")

            # for each result on this page, create new movie entry in database if doesn't already exist
            for result in response_json['results']:
                movie_info = {
                    'tmdb_id': result['id'],
                    #'imdb_id': "zz" + str(result['id']),
                    'poster_url': result['poster_path'],
                    'title': result['name'][:255],
                    'rating': result['vote_average'],
                    'release_date': '9999-01-01' if result['first_air_date'] == '' else result['first_air_date'],
                    'description': result['overview'][:255],
                    'origin_location': '',
                    'languages': result['original_language'],
                    'genres': result['genre_ids'],
                    #'last_updated': datetime.now().date(),
                    'run_time': 0,
                    'media_type': result['media_type'],
                }
                recommendation_list.append(movie_info)

            # go to next page
            page += 1
            url = f"{base_url}?include_adult=false&language=en-US&page={page}&sort_by=popularity.desc"
            #url = f"{base_url}?include_adult=false&language=en-US&page={page}"
            response = requests.get(url, headers=headers)
            response_json = response.json()

    print("===== End of recommendations =====")
    
    return recommendation_list


# load data for tv shows from TMDB
def load_tv_data_TMDB():
    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }
    
    # get all tv shows
    tvshows = TVShows.objects.all()

    print("===== Starting tv show detail setup =====")
    tvshow_count = 1

    for tvshow in tvshows:
        print(f"===== TV Show #{tvshow_count}: {tvshow.title}")
        actor_list = []
        director_list = []
        genre_list = []
        trailer_list = []

        # url to get the details about a tv show
        url = f"https://api.themoviedb.org/3/tv/{tvshow.tmdb_id}?language=en-US&append_to_response=videos,images,credits"
        response = requests.get(url, headers=headers)
        response_json = response.json()

        # update imdb_id
        if tvshow.imdb_id is not None and tvshow.imdb_id != '':
            if tvshow.imdb_id == int(tvshow.imdb_id[2:]):
                tvshow.imdb_id = response_json['imdb_id']

        # update seasons 
        if tvshow.seasons == 0:
            tvshow.seasons = response_json['number_of_seasons']

        # update status
        tvshow.status = response_json['status']

        # people credits
        credits = response_json['credits']

        # trailers
        trailers = response_json['videos']

        # genres
        genres = response_json['genres']

        # foreach tv show get the credits then actors and directors
        for result in credits['cast']:
            existing_person = Peoples.objects.filter(tmdb_id=result['id']).first()
            if existing_person is not None:
                # check if we already have a many to many relationship with this person for the movie
                actor_exists = tvshow.actors_cast.filter(id=existing_person.id).exists()
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
        
        # foreach tv show get the trailers
        for trailer in trailers['results']:
            existing_trailer = Trailers.objects.filter(video_id=trailer['id']).first()
            if existing_trailer is not None:
                # check if we already have a many to many relationship with this trailer for the movie
                trailer_exists = tvshow.youtube_trailer.filter(id=existing_trailer.id).exists()
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

        # update movie foreign keys/many to many relationships
        if len(actor_list) > 0:
            tvshow.actors_cast.set(actor_list)

        if len(director_list) > 0:
            tvshow.director.set(director_list)

        if len(trailer_list) > 0:
            tvshow.youtube_trailer.set(trailer_list)

        if len(genre_list) > 0:
            tvshow.genres.set(genre_list)

        tvshow.save()
        tvshow_count += 1

    return True