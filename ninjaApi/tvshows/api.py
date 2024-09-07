from datetime import date, datetime, timedelta
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
import requests
from genres.api import Genre
from backendApi.utils.helper import calculate_day_difference
from genres.models import Genres
from movies.models import Movies
from people.models import Peoples
from trailers.models import Trailers
from people.api import People
from trailers.api import Trailer
from tvshows.models import Episodes, TVShows
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

class TVShowEpisode(Schema):
    tmdb_id: int
    still_path: str | None = None
    name: str
    rating: float | None = None
    release_date: date | None = None
    description: str
    origin_location: str | None = None
    episode_number: int
    runtime: int | None = None
    season_number: int
    episode_type: str
    enabled: bool
    expires: datetime | None = None

class TVShowOut(Schema):
    id: UUID
    tmdb_id: int
    imdb_id: str
    poster_url: str | None = None
    title: str
    rating: float | None = None
    release_date: date | None = None
    description: str
    origin_location: str | None = None
    languages: str
    imdb_link: str
    youtube_trailer: List[Trailer]
    actors_cast: List[People]
    director: List[People]
    genres: List[Genre]
    recommendations: List[TVShowRecommendations] | None = None
    episodes: List[TVShowEpisode] | None = None
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
    skip_round_2 = False

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

@router.get("/seeding/data/{tmdb_id}")
def tvshows_data_loading(request, tmdb_id: int):
    # TODO load data from other sources too
    load_single_tv_show_data_TMDB(tmdb_id)
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
    episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
    tv_show.episodes = episodes
    return tv_show

# get tv show by tmdb_id
@router.get("/tmdb_id/{tmdb_id}", response=TVShowOut)
def get_tv_by_tmdb_id(request, tmdb_id: int):
    tv_show = get_object_or_404(TVShows, tmdb_id=tmdb_id)
    tv_show.recommendations = get_tv_recommendations_logic_TMDB(tmdb_id)
    episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
    tv_show.episodes = episodes
    return tv_show
    

# get tv show by imdb_id
@router.get("/imdb_id/{imdb_id}", response=TVShowOut)
def get_tv_show_by_imdb_id(request, imdb_id: str):
    tv_show = get_object_or_404(TVShows, imdb_id=imdb_id)
    tv_show.recommendations = get_tv_recommendations_logic_TMDB(imdb_id)
    episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
    tv_show.episodes = episodes
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
    ).all()[:100]

    # get episodes for season 1 by default
    for tv_show in tv_show_list:
        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
        tv_show.episodes = episodes

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
    ).filter(title__icontains=title_str)[:100]

    # get episodes for season 1 by default
    for tv_show in shows_list:
        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
        tv_show.episodes = episodes

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


@router.get("/newly-released/", response=List[TVShowOut])
def get_newly_released_movies_TMDB(request):
    return fetch_tv_shows_new_releases_TMDB()

@router.get("/trending/daily/", response=List[TVShowOut])
def get_trending_movies_daily_TMDB(request):
    return fetch_tv_shows_trending_daily_TMDB()

@router.get("/trending/weekly/", response=List[TVShowOut])
def get_trending_movies_weekly_TMDB(request):
    return fetch_tv_shows_trending_weekly_TMDB()

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
                            tvshow_exists.poster_url = result['poster_path']
                            tvshow_exists.title = result['name']
                            tvshow_exists.rating = result['vote_average']
                            tvshow_exists.description = result['overview'][:255]
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
                            tvshow_exists.poster_url = result['poster_path']
                            tvshow_exists.title = result['name']
                            tvshow_exists.rating = result['vote_average']
                            tvshow_exists.release_date = result['first_air_date']
                            tvshow_exists.description = result['overview'][:255]
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

        # foreach season get the episodes
        season_count = 1
        while season_count <= tvshow.seasons:
            fetch_episodes_for_season_TMDB(tvshow.tmdb_id, season_count)
            season_count += 1

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

# get the details for a tv show from TMDB
def load_single_tv_show_data_TMDB(tmdb_id):
    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }
    
    # get all tv shows
    tv_show = TVShows.objects.filter(tmdb_id=tmdb_id).first()
    if tv_show is None:
        return False

    actor_list = []
    director_list = []
    genre_list = []
    trailer_list = []

    # url to get the details about a movie
    url = f"https://api.themoviedb.org/3/tv/{tv_show.tmdb_id}?language=en-US&append_to_response=videos,images,credits"
    response = requests.get(url, headers=headers)
    response_json = response.json()

    # update imdb_id
    if tv_show.imdb_id is not None and tv_show.imdb_id != '':
        if tv_show.imdb_id == int(tv_show.imdb_id[2:]):
            tv_show.imdb_id = response_json['imdb_id']

    # update status
    if "status" in response_json:
        tv_show.status = response_json['status']

    # update seasons
    if "number_of_seasons" in response_json and tv_show.seasons <= 0:
        tv_show.seasons = response_json['number_of_seasons']  

    # update backdrop
    if "backdrop_path" in response_json and tv_show.backdrop_url is None:
        tv_show.backdrop_url = response_json['backdrop_path']

    # people credits
    #credits = []
    if "credits" in response_json:
        credits = response_json['credits']

    # trailers
    #trailers =[]
    if "videos" in response_json:
        trailers = response_json['videos']

    # genres
    #genres = []
    if "genres" in response_json:
        genres = response_json['genres']

    # foreach movie get the credits then actors and directors
    for result in credits['cast']:
        existing_person = Peoples.objects.filter(tmdb_id=result['id']).first()
        if existing_person is not None:
            # check if we already have a many to many relationship with this person for the movie
            actor_exists = tv_show.actors_cast.filter(id=existing_person.id).exists()
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

    # foreach movie get the genres
    for genre in genres:
        existing_genre = Genres.objects.filter(tmdb_id=genre['id']).first()
        if existing_genre is not None:
            # check if we already have a many to many relationship with this genre for the movie
            genre_exists = tv_show.genres.filter(id=existing_genre.id).exists()
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
    
    # foreach movie get the trailers
    for trailer in trailers['results']:
        existing_trailer = Trailers.objects.filter(video_id=trailer['id']).first()
        if existing_trailer is not None:
            # check if we already have a many to many relationship with this trailer for the movie
            trailer_exists = tv_show.youtube_trailer.filter(id=existing_trailer.id).exists()
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

    # foreach season get the episodes
    season_count = 1
    while season_count <= tv_show.seasons:
        fetch_episodes_for_season_TMDB(tmdb_id, season_count)
        season_count += 1

    # update movie foreign keys/many to many relationships
    if len(actor_list) > 0:
        tv_show.actors_cast.set(actor_list)

    if len(director_list) > 0:
        tv_show.director.set(director_list)

    if len(trailer_list) > 0:
        tv_show.youtube_trailer.set(trailer_list)

    if len(genre_list) > 0:
        tv_show.genres.set(genre_list)

    tv_show.save()

    return True

# get episodes for a season for a tv show from TMDB
def fetch_episodes_for_season_TMDB(tmdb_id, season_number):
    base_url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_number}?language=en-US"
    episode_list = []

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    response = requests.get(base_url, headers=headers)
    response_json = response.json()

    if "episodes" in response_json:
        for episode in response_json["episodes"]:
            # get tv show
            tv_show = TVShows.objects.filter(tmdb_id=episode['show_id']).first()

            # setup episode info
            episode_info = {
                'tmdb_id': episode['id'],
                'tv_show_tmdb_id': episode['show_id'],
                'release_date': episode['air_date'],
                'episode_number': episode['episode_number'],
                'name': episode['name'][:255],
                'description': episode['overview'][:255],
                'runtime': episode['runtime'],
                'season_number': episode['season_number'],
                'still_path': episode['still_path'],
                'rating': episode['vote_average'],
                'episode_type': episode['episode_type'],
                'enabled': True,
            }

            # check if episode doesn't already exist
            episode_exists = Episodes.objects.filter(tmdb_id=episode['id']).first()
            if episode_exists and episode_exists.last_updated is not None:
                if calculate_day_difference(episode_exists.last_updated.strftime('%Y-%m-%d'), 7):
                    # update movie entry
                    episode_exists.tmdb_id = episode['id']
                    episode_exists.still_path = episode['still_path']
                    episode_exists.name = episode['name']
                    episode_exists.rating = episode['vote_average']
                    episode_exists.release_date = episode['air_date']
                    episode_exists.description = episode['overview'][:255]
                    episode_exists.save()

                episode_list.append(episode_exists)
            elif episode_exists is None:
                # create new episode entry
                episode = Episodes.objects.create(**episode_info)
                episode.tv_show_id.add(tv_show)
                episode.save()

                episode_list.append(episode)
            else:
                continue # skip

    return True

# get newly released tv shows from TMDB
def fetch_tv_shows_new_releases_TMDB():
    two_months_ago = datetime.now() - timedelta(days=60)
    today = datetime.now()

    base_url = f"https://api.themoviedb.org/3/discover/tv?first_air_date.gte={two_months_ago.strftime('%Y-%m-%d')}&first_air_date.lte={today.strftime('%Y-%m-%d')}&include_adult=false&include_null_first_air_dates=false&language=en-US&sort_by=popularity.desc"
    page = 1
    max_pages = 10 # TMDB limits us to 500 pages
    tv_show_list = []

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    # get based on newly released, popular sort by descending (highest popularity to least popularity) 

    print("===== Fetching newly released tv shows =====")
    url = f"{base_url}&page={page}"

    response = requests.get(url, headers=headers)
    response_json = response.json()

    if response_json['total_pages'] > 1:
        # get all the pages we can get
        while page <= max_pages:
            #print("===== Page " + str(page) + " =====")

            # for each result on this page, create new movie entry in database if doesn't already exist
            for result in response_json['results']:
                tv_show_info = {
                    'tmdb_id': result['id'],
                    'imdb_id': "zz" + str(result['id']),
                    'poster_url': result['poster_path'],
                    'backdrop_url': result['backdrop_path'],
                    'title': result['title'][:255],
                    'rating': result['vote_average'],
                    'release_date': '9999-01-01' if result['release_date'] == '' else result['release_date'],
                    'description': result['overview'][:255],
                    'origin_location': '',
                    'languages': result['original_language'],
                    'imdb_link': '',
                    'last_updated': datetime.now().date(),
                    #'genres': [],
                    'enabled': True,
                    #'expires': datetime.now(),
                    #'youtube_trailer': [],
                    #'run_time': result["runtime"],
                }

                # check if movie doesn't already exist
                tv_show_exists = TVShows.objects.prefetch_related(
                    'youtube_trailer',
                    'actors_cast',
                    'director',
                    'genres',
                    'reviews'
                ).filter(tmdb_id=result['id']).first()
                if tv_show_exists and tv_show_exists.last_updated is not None:
                    if calculate_day_difference(tv_show_exists.last_updated.strftime('%Y-%m-%d'), 7):
                        # update movie entry
                        tv_show_exists.tmdb_id = result['id']
                        tv_show_exists.poster_url = result['poster_path']
                        tv_show_exists.title = result['title']
                        tv_show_exists.rating = result['vote_average']
                        tv_show_exists.release_date = result['release_date']
                        tv_show_exists.description = result['overview'][:255]
                        #movie_exists.run_time = result['runtime']
                        tv_show_exists.last_updated = datetime.now().date()
                        tv_show_exists.save()

                    # get episodes
                    episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show_exists.tmdb_id, season_number=1)
                    tv_show_exists.episodes = episodes

                    tv_show_list.append(tv_show_exists)
                elif tv_show_exists is None:
                    # create new movie entry
                    tv_show = TVShows.objects.create(**tv_show_info)
                    
                    # assign genres
                    genres = Genres.objects.filter(tmdb_id__in=result['genre_ids'])
                    tv_show.genres.set(genres)

                    # assign trailers
                    #movie.youtube_trailer.set()

                    tv_show.save()

                    load_single_tv_show_data_TMDB(tv_show.tmdb_id)
                    tv_show_full = TVShows.objects.prefetch_related(
                        'youtube_trailer',
                        'actors_cast',
                        'director',
                        'genres',
                        'reviews'
                    ).filter(tmdb_id=tv_show.tmdb_id).first()

                    if tv_show_full is not None:
                        # get episodes
                        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
                        tv_show_full.episodes = episodes
                        tv_show_list.append(tv_show_full)
                else:
                    continue # skip

            # go to next page
            page += 1
            url = f"{base_url}&page={page}"
            response = requests.get(url, headers=headers)
            response_json = response.json()

        print("===== End of newly released tv shows =====")

    return tv_show_list

# fetch trending now tv shows from TMDB (weekly trending)
def fetch_tv_shows_trending_weekly_TMDB():
    base_url = "https://api.themoviedb.org/3/trending/tv/week"
    page = 1
    max_pages = 10 # TMDB limits us to 500 pages
    tv_show_list = []

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    print("===== Fetching trending weekly tv shows =====")
    url = f"{base_url}?include_adult=false&language=en-US&page={page}"

    response = requests.get(url, headers=headers)
    response_json = response.json()

    if response_json['total_pages'] > 1:
        # get all the pages we can get
        while page <= max_pages:
            print("===== Page " + str(page) + " =====")

            # for each result on this page, create new tv show entry in database if doesn't already exist
            for result in response_json['results']:
                tv_show_info = {
                    'tmdb_id': result['id'],
                    'imdb_id': "zz" + str(result['id']),
                    'poster_url': result['poster_path'],
                    'backdrop_url': result['backdrop_path'],
                    'title': result['name'][:255],
                    'rating': result['vote_average'],
                    'release_date': '9999-01-01' if result['first_air_date'] == '' else result['first_air_date'],
                    'description': result['overview'][:255],
                    'origin_location': '',
                    'languages': result['original_language'],
                    'imdb_link': '',
                }

                # check if tv show doesn't already exist
                tv_show_exists = TVShows.objects.prefetch_related(
                    'youtube_trailer',
                    'actors_cast',
                    'director',
                    'genres',
                    'reviews'
                ).filter(tmdb_id=result['id']).first()
                if tv_show_exists and tv_show_exists.last_updated is not None:
                    if calculate_day_difference(tv_show_exists.last_updated.strftime('%Y-%m-%d'), 7):
                        # update movie entry
                        tv_show_exists.poster_url = result['poster_path']
                        tv_show_exists.title = result['name']
                        tv_show_exists.rating = result['vote_average']
                        tv_show_exists.description = result['overview'][:255]
                        tv_show_exists.save()

                    # get episodes
                    episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show_exists.tmdb_id, season_number=1)
                    tv_show_exists.episodes = episodes

                    tv_show_list.append(tv_show_exists)
                elif tv_show_exists is None:
                    # create new movie entry
                    tv_show = TVShows.objects.create(**tv_show_info)

                    # assign genres
                    genres = Genres.objects.filter(tmdb_id__in=result['genre_ids'])
                    tv_show.genres.set(genres)
                    tv_show.save()

                    load_single_tv_show_data_TMDB(tv_show.tmdb_id)
                    tv_show_full = TVShows.objects.prefetch_related(
                        'youtube_trailer',
                        'actors_cast',
                        'director',
                        'genres',
                        'reviews'
                    ).filter(tmdb_id=tv_show.tmdb_id).first()

                    if tv_show_full is not None:
                        # get episodes
                        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
                        tv_show_full.episodes = episodes
                        tv_show_list.append(tv_show_full)
                else:
                    continue # skip

            # go to next page
            page += 1
            url = f"{base_url}?include_adult=false&language=en-US&page={page}"
            response = requests.get(url, headers=headers)
            response_json = response.json()

        print("===== End of trending weekly tv shows =====")
    
    return tv_show_list

# fetch top picks today tv shows from TMDB (today's trending)
def fetch_tv_shows_trending_daily_TMDB():
    base_url = "https://api.themoviedb.org/3/trending/tv/day"
    page = 1
    max_pages = 10 # TMDB limits us to 500 pages
    tv_show_list = []

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    print("===== Fetching trending daily tv shows =====")
    url = f"{base_url}?include_adult=false&language=en-US&page={page}"

    response = requests.get(url, headers=headers)
    response_json = response.json()

    if response_json['total_pages'] > 1:
        # get all the pages we can get
        while page <= max_pages:
            print("===== Page " + str(page) + " =====")

            for result in response_json['results']:
                tv_show_info = {
                    'tmdb_id': result['id'],
                    'imdb_id': "zz" + str(result['id']),
                    'poster_url': result['poster_path'],
                    'backdrop_url': result['backdrop_path'],
                    'title': result['name'][:255],
                    'rating': result['vote_average'],
                    'release_date': '9999-01-01' if result['first_air_date'] == '' else result['first_air_date'],
                    'description': result['overview'][:255],
                    'origin_location': '',
                    'languages': result['original_language'],
                    'imdb_link': '',
                }

                # check if tv show doesn't already exist
                tv_show_exists = TVShows.objects.prefetch_related(
                    'youtube_trailer',
                    'actors_cast',
                    'director',
                    'genres',
                    'reviews'
                ).filter(tmdb_id=result['id']).first()
                if tv_show_exists and tv_show_exists.last_updated is not None:
                    if calculate_day_difference(tv_show_exists.last_updated.strftime('%Y-%m-%d'), 7):
                        # update movie entry
                        tv_show_exists.poster_url = result['poster_path']
                        tv_show_exists.title = result['name']
                        tv_show_exists.rating = result['vote_average']
                        tv_show_exists.description = result['overview'][:255]
                        tv_show_exists.save()

                    # get episodes
                    episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show_exists.tmdb_id, season_number=1)
                    tv_show_exists.episodes = episodes

                    tv_show_list.append(tv_show_exists)
                elif tv_show_exists is None:
                    # create new movie entry
                    tv_show = TVShows.objects.create(**tv_show_info)

                    # assign genres
                    genres = Genres.objects.filter(tmdb_id__in=result['genre_ids'])
                    tv_show.genres.set(genres)
                    tv_show.save()

                    load_single_tv_show_data_TMDB(tv_show.tmdb_id)
                    tv_show_full = TVShows.objects.prefetch_related(
                        'youtube_trailer',
                        'actors_cast',
                        'director',
                        'genres',
                        'reviews'
                    ).filter(tmdb_id=tv_show.tmdb_id).first()

                    if tv_show_full is not None:
                        # get episodes
                        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
                        tv_show_full.episodes = episodes

                        tv_show_list.append(tv_show_full)
                else:
                    continue # skip

            # go to next page
            page += 1
            url = f"{base_url}?include_adult=false&language=en-US&page={page}"
            response = requests.get(url, headers=headers)
            response_json = response.json()

        print("===== End of trending daily tv shows =====")

    return tv_show_list