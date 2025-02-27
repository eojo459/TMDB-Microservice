from datetime import date, datetime, timedelta
import json
from typing import List
from uuid import UUID
from django.forms import model_to_dict
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
from tvshows.models import Episodes, TVShows, TVShowsNewReleases, TVShowsTrendingAmazonPrime, TVShowsTrendingDaily, TVShowsTrendingDisneyPlus, TVShowsTrendingNetflix, TVShowsTrendingWeekly
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
    imdb_link: str | None = None
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
    genres: List[Genre] | None = None
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
    id: UUID | None = None
    tmdb_id: int
    imdb_id: str
    poster_url: str | None = None
    title: str
    rating: float | None = None
    release_date: date | None = None
    description: str
    origin_location: str | None = None
    languages: str
    imdb_link: str | None = None
    youtube_trailer: List[Trailer]
    actors_cast: List[People]
    director: List[People]
    genres: List[Genre]
    recommendations: List[TVShowRecommendations] | None = None
    episodes: List[TVShowEpisode] | None = None
    seasons: int
    enabled: bool
    media_type: str | None = None
    expires: datetime | None = None
    type: str = "tv"

class MovieOut(Schema):
    id: UUID
    tmdb_id: int
    imdb_id: str
    poster_url: str
    title: str
    rating: float
    release_date: date | str | None = None
    description: str
    origin_location: str
    languages: str
    imdb_link: str | None = None
    run_time: int 
    enabled: bool
    type: str = "movie"
    #expires: datetime

class Season(Schema):
    tmdb_id: int
    release_date: date | None = None
    episode_number: int
    name: str
    description: str
    runtime: int | None = None
    season_number: int
    tv_show_tmdb_id: int
    still_path: str | None = None
    rating: float | None = None
    #vote_count: int | None = None

class WatchlistItem(Schema):
    imdb_id: str
    tmdb_id: str
    type: str
    updated_at: str
    created_at: str
    watchlist_id: str

class Watchlist(Schema):
    watchlist_id: str
    items: List[object] | None

class TrendingServicesTV(Schema):
    netflix_tv_shows: List[TVShowOut] | None = None
    amazon_prime_tv_shows: List[TVShowOut] | None = None
    disney_plus_tv_shows: List[TVShowOut] | None = None
    

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
def tvshows_data_loading_single(request, tmdb_id: int):
    # TODO load data from other sources too
    return load_single_tv_show_data_TMDB(tmdb_id)[1]

# create new tv show
@router.post("/", auth=None)
def create_tv_show(request, payload: TVShow):
    tv_show = TVShows.objects.create(**payload.dict())
    return {"id": tv_show.id}

# get tv show by id
@router.get("/id/{id}", response=TVShowOut)
def get_tv_show_by_id(request, id: str):
    tv_show = get_object_or_404(TVShows, id=id)
    #tv_show.recommendations = get_tv_recommendations_logic_TMDB(id)
    episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
    if episodes.count() <= 0:
        # get episodes
        episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

    tv_show.episodes = episodes
    return tv_show

# get tv show by tmdb_id
@router.get("/tmdb_id/{tmdb_id}", response=TVShowOut)
def get_tv_by_tmdb_id(request, tmdb_id: int):
    tv_show = TVShows.objects.filter(tmdb_id=tmdb_id).first()
    if tv_show is None:
        # create new tv show
        if load_single_tv_show_data_TMDB(tmdb_id):
            tv_show = TVShows.objects.filter(tmdb_id=tmdb_id).first()

    # update tv show if seasons == 0
    if tv_show.seasons == 0 or tv_show.episodes == 0:
        load_single_tv_show_data_TMDB(tmdb_id, True)

    # TEMP 
    skip_episodes = False
    if skip_episodes == False:
        episodes = Episodes.objects.filter(tv_show_id=tv_show.id, season_number=1)
        if episodes.count() <= 0:
            # update tv show
            load_single_tv_show_data_TMDB(tmdb_id, True)

            # get updated tv show
            tv_show = TVShows.objects.filter(tmdb_id=tmdb_id).first()

            # get episodes
            episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

        tv_show.episodes = episodes
    else:
        tv_show.episodes = []

    tv_show.recommendations = get_tv_recommendations_logic_TMDB(tmdb_id)
    
    return tv_show

# get media (tv or movie) by tmdb_id
@router.get("/media/tmdb_id/{tmdb_id}", response=TVShowOut | MovieOut)
def get_media_by_tmdb_id(request, tmdb_id: int):
    # try to get tv show first
    tv_show = TVShows.objects.filter(tmdb_id=tmdb_id).first()
    if tv_show is None:
        # try movie
        movie = Movies.objects.filter(tmdb_id=tmdb_id).first()
        movie.type = "movie"
        return movie

    # update tv show if seasons == 0
    if tv_show.seasons == 0 or tv_show.episodes == 0:
        load_single_tv_show_data_TMDB(tmdb_id, True)

    # TEMP 
    skip_episodes = False
    if skip_episodes == False:
        episodes = Episodes.objects.filter(tv_show_id=tv_show.id, season_number=1)
        if episodes.count() <= 0:
            # update tv show
            load_single_tv_show_data_TMDB(tmdb_id, True)

            # get updated tv show
            tv_show = TVShows.objects.filter(tmdb_id=tmdb_id).first()

            # get episodes
            episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

        tv_show.episodes = episodes
    else:
        tv_show.episodes = []

    tv_show.type = "tv"
    #tv_show.recommendations = get_tv_recommendations_logic_TMDB(tmdb_id)
    
    return tv_show

# get list of tv show by tmdb_id
@router.post("/tmdb_ids/", response=List[TVShowOut])
def get_list_of_tv_by_tmdb_id(request, payload: List[object]):
    if request.method != 'POST':
        return 405, {"detail": "Method not allowed."}
    
    tv_show_list = []

    for item in payload:
        tmdb_id = item['tmdb_id']

        tv_show = TVShows.objects.filter(tmdb_id=tmdb_id).first()
        if tv_show is None:
            # create new tv show
            if load_single_tv_show_data_TMDB(tmdb_id):
                tv_show = TVShows.objects.filter(tmdb_id=tmdb_id).first()

        # update tv show if seasons == 0
        if tv_show.seasons == 0 or tv_show.episodes == 0:
            load_single_tv_show_data_TMDB(tmdb_id, True)

        # TEMP 
        skip_episodes = True
        if skip_episodes == False:
            episodes = Episodes.objects.filter(tv_show_id=tv_show.id, season_number=1)
            if episodes.count() <= 0:
                # update tv show
                load_single_tv_show_data_TMDB(tmdb_id, True)

                # get updated tv show
                tv_show = TVShows.objects.filter(tmdb_id=tmdb_id).first()

                # get episodes
                episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

            tv_show.episodes = episodes
        else:
            tv_show.episodes = []

        #tv_show.recommendations = get_tv_recommendations_logic_TMDB(tmdb_id)
        tv_show.type = "tv"
        tv_show_list.append(tv_show)
    
    return tv_show_list
    

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
def get_newly_released_tv_shows_TMDB(request):
   cached_data = fetch_tv_shows_new_releases_cached()

   if len(cached_data) > 0:
       return cached_data
   
   return fetch_tv_shows_new_releases_TMDB()

@router.get("/trending/daily/", response=List[TVShowOut])
def get_trending_tv_shows_daily_TMDB(request):
    cached_data = fetch_tv_shows_trending_daily_cached()

    if len(cached_data) > 0:
        return cached_data
    
    return fetch_tv_shows_trending_daily_TMDB()

@router.get("/trending/weekly/", response=List[TVShowOut])
def get_trending_tv_shows_weekly_TMDB(request):
    cached_data = fetch_tv_shows_trending_weekly_cached()

    if len(cached_data) > 0:
        return cached_data
    
    return fetch_tv_shows_trending_weekly_TMDB()

# delete all tv show episodes
# only for testing
# @router.delete("/delete/episodes/all/")
# def delete_tv_show_episodes_by_imdb_id(request):
#     all_tv_shows = Episodes.objects.all()

#     for tv_show in all_tv_shows:
#         tv_show.archived = True
#         tv_show.save()

#     return {"success": True}

# get episode data for a tv show
@router.get("/tmdb_id/{tmdb_id}/season/{season_number}/episode/{episode_number}", response=List[Season])
def get_tv_shows_season_episode_TMDB(request, tmdb_id: int, season_number: int, episode_number: int):
    return get_tv_season_episodes_TMDB(tmdb_id, season_number, episode_number)

# get all episodes in a season for a tv show
@router.get("/tmdb_id/{tmdb_id}/season/{season_number}", response=List[Season])
def get_tv_shows_season_TMDB(request, tmdb_id: int, season_number: int):
    return get_tv_season_episodes_TMDB(tmdb_id, season_number)

@router.get("/trending/streaming/", response=TrendingServicesTV)
def get_trending_tv_shows_streaming_services(request):
    cached_data = fetch_tv_shows_trending_services_cached()

    if len(cached_data) > 0:
        return cached_data
    
    return fetch_tv_shows_trending_services()

@router.get("/trending/netflix/", response=List[TVShowOut])
def get_trending_tv_shows_netflix(request):
    cached_data = fetch_tv_shows_trending_netflix_cached()

    if len(cached_data) > 0:
        return cached_data
    
    data = fetch_tv_shows_trending_services()
    return data["netflix_tv_shows"]

@router.get("/trending/disney_plus/", response=List[TVShowOut])
def get_trending_tv_shows_disney_plus(request):
    cached_data = fetch_tv_shows_trending_disney_plus_cached()

    if len(cached_data) > 0:
        return cached_data
    
    data = fetch_tv_shows_trending_services()
    return data["disney_plus_tv_shows"]

@router.get("/trending/amazon_prime/", response=List[TVShowOut])
def get_trending_tv_shows_amazon_prime(request):
    cached_data = fetch_tv_shows_trending_amazon_prime_cached()

    if len(cached_data) > 0:
        return cached_data
    
    data = fetch_tv_shows_trending_services()
    return data["amazon_prime_tv_shows"]

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
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
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
                        'languages': result['original_language'],
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
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
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

    # load genres with data
    for item in recommendation_list:
        item['genres'] = load_tv_show_genres(item['genres'])
    
    return recommendation_list


# load data for tv shows from TMDB
def load_tv_data_TMDB():
    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
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
def load_single_tv_show_data_TMDB(tmdb_id, update=False, load_seasons=False):
    # check if tv show already exists
    existing_tv_show = TVShows.objects.filter(tmdb_id=tmdb_id).first()
    if existing_tv_show is not None and update == False:
        return False, existing_tv_show
    
    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
    }

    actor_list = []
    director_list = []
    genre_list = []
    trailer_list = []

    # url to get the details about a movie
    url = f"https://api.themoviedb.org/3/tv/{tmdb_id}?language=en-US&append_to_response=videos,images,credits"
    response = requests.get(url, headers=headers)
    response_json = response.json()

    if existing_tv_show is not None and update == True:
        # update tv show
        existing_tv_show.title = response_json['name']
        existing_tv_show.tmdb_id = response_json['id']
        existing_tv_show.description = response_json['overview'][:252] + "..." if len(response_json['overview']) > 255 else response_json['overview'][:255]
        existing_tv_show.poster_url = response_json['poster_path']
        existing_tv_show.backdrop_url = response_json['backdrop_path']
        existing_tv_show.seasons = response_json['number_of_seasons']
        existing_tv_show.episodes = response_json['number_of_episodes']
        existing_tv_show.rating = response_json['vote_average']
        existing_tv_show.release_date = response_json['first_air_date']
        existing_tv_show.languages = response_json['original_language']
        existing_tv_show.imdb_link = ''
        existing_tv_show.save()
        return True, existing_tv_show

    # create new tv show
    new_tv_show = {
        'tmdb_id': response_json['id'],
        'imdb_id': "zz" + str(response_json['id']),
        'title': response_json['name'],
        #'original_title': response_json['original_name'],
        'description': response_json['overview'][:252] + "..." if len(response_json['overview']) > 255 else response_json['overview'][:255],
        'poster_url': response_json['poster_path'],
        'backdrop_url': response_json['backdrop_path'],
        'seasons': response_json['number_of_seasons'],
        'episodes': response_json['number_of_episodes'],
        'rating': response_json['vote_average'],
        #'vote_count': response_json['vote_count'],
        'release_date': response_json['first_air_date'],
        'languages': response_json['original_language'],
        'imdb_link': '',
    }                        
                        
    # create the new tv show
    tv_show = TVShows.objects.create(**new_tv_show)

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

    if load_seasons:
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

    return True, tv_show

# get episodes for a season for a tv show from TMDB
def fetch_episodes_for_season_TMDB(tmdb_id, season_number):
    base_url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_number}?language=en-US"
    episode_list = []

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
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
                'tv_show_id': tv_show,
                'release_date': episode['air_date'],
                'episode_number': episode['episode_number'],
                'name': episode['name'][:255],
                'description': episode['overview'][:252] + "..." if len(episode['overview']) > 255 else episode['overview'][:255],
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

                #episode_list.append(episode_exists)
            elif episode_exists is None:
                # create new episode entry
                episode = Episodes.objects.create(**episode_info)
                #episode_list.append(episode)
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
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
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
                    'title': result['name'][:255],
                    'rating': result['vote_average'],
                    'release_date': '9999-01-01' if result['first_air_date'] == '' else result['first_air_date'],
                    'description': result['overview'][:255],
                    'languages': result['original_language'],
                    'imdb_link': '',
                    'origin_location': '',
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
                        tv_show_exists.poster_url = result['poster_path']
                        tv_show_exists.title = result['name']
                        tv_show_exists.rating = result['vote_average']
                        tv_show_exists.release_date = result['first_air_date']
                        tv_show_exists.description = result['overview'][:255]
                        tv_show_exists.save()

                    # get episodes
                    episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show_exists.tmdb_id, season_number=1)
                    if episodes.count() <= 0:
                        # get episodes
                        season_episodes = get_tv_season_episodes_TMDB(tv_show_info['tmdb_id'], 1)
                        tv_show_exists.episodes = season_episodes
                    else:
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
                        if episodes.count() <= 0:
                            # get episodes
                            season_episodes = get_tv_season_episodes_TMDB(tv_show_info['tmdb_id'], 1)
                            tv_show_full.episodes = season_episodes
                        else:
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

    # update new releases cache
    tv_shows_new_releases = TVShowsNewReleases.objects.all()
    for item in tv_shows_new_releases:
        if item.tmdb_id not in [tv_show.tmdb_id for tv_show in tv_show_list]:
            item.delete()

    for index, tv_show in enumerate(tv_show_list[:50]):
        if TVShowsNewReleases.objects.filter(tmdb_id=tv_show.tmdb_id).first() == None:
            # create new release
            data = {
                'tmdb_id': tv_show.tmdb_id,
                'imdb_id': tv_show.imdb_id,
                'rank': index + 1
            }
            TVShowsNewReleases.objects.create(**data)

    return tv_show_list

# fetch trending now tv shows from TMDB (weekly trending)
def fetch_tv_shows_trending_weekly_TMDB(page_max=10):
    base_url = "https://api.themoviedb.org/3/trending/tv/week"
    page = 1
    max_pages = page_max # TMDB limits us to 500 pages
    tv_show_list = []

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
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
                    'languages': result['original_language'],
                    'imdb_link': '',
                    'origin_location': '',
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
    
    # update trending weekly cache
    tv_shows_trending_weekly = TVShowsTrendingWeekly.objects.all()
    for item in tv_shows_trending_weekly:
        if item.tmdb_id not in [tv_show.tmdb_id for tv_show in tv_show_list]:
            item.delete()

    for index, tv_show in enumerate(tv_show_list[:50]):
        if TVShowsTrendingWeekly.objects.filter(tmdb_id=tv_show.tmdb_id).first() == None:
            # create new trending weekly
            data = {
                'tmdb_id': tv_show.tmdb_id,
                'imdb_id': tv_show.imdb_id,
                'rank': index + 1
            }
            TVShowsTrendingWeekly.objects.create(**data)

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
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
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
                    'languages': result['original_language'],
                    'imdb_link': '',
                    'origin_location': '',
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

    # update trending daily cache
    tv_shows_trending_daily = TVShowsTrendingDaily.objects.all()
    for item in tv_shows_trending_daily:
        if item.tmdb_id not in [tv_show.tmdb_id for tv_show in tv_show_list]:
            item.delete()

    for index, tv_show in enumerate(tv_show_list[:50]):
        if TVShowsTrendingDaily.objects.filter(tmdb_id=tv_show.tmdb_id).first() == None:
            # create new trending daily
            data = {
                'tmdb_id': tv_show.tmdb_id,
                'imdb_id': tv_show.imdb_id,
                'rank': index + 1
            }
            TVShowsTrendingDaily.objects.create(**data)

    return tv_show_list


# get season episodes for the tv show
def get_tv_season_episodes_TMDB(series_id, season_number, episode_number = None, update = False):
    episode_list = []

    # if update == False:
    #     # get local episodes if they exist
    #     episodes_exists = Episodes.objects.filter(tv_show_tmdb_id=series_id)
    #     if len(episodes_exists) > 0:
    #         for episode in episodes_exists:
    #             episode_list.append(episode)

    #         # sort episodes from episode 1 down (ascending order)
    #         episode_list = sorted(episode_list, key=lambda x: x.episode_number)
            
    #         return episode_list

    if season_number <= 0 or season_number is None:
        season_number = 1

    if episode_number is not None:
        url = f"https://api.themoviedb.org/3/tv/{series_id}/season/{season_number}/episode/{episode_number}"
    else:
        # get all episodes in the season
        url = f"https://api.themoviedb.org/3/tv/{series_id}/season/{season_number}"

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
    }

    #print(f"===== Getting season {season_number} for {series_id} =====")

    response = requests.get(url, headers=headers)
    response_json = response.json()
    default_runtime = None

    if episode_number is not None:
        if default_runtime == None and response_json['runtime'] is not None and response_json['runtime'] > 0:
            default_runtime = response_json['runtime']

        episode_info = {
            'tmdb_id': response_json['id'],
            'episode_number': response_json['episode_number'],
            'name': response_json['name'][:255],
            'description': response_json['overview'][:252] + "...",
            'runtime': response_json['runtime'] if response_json['runtime'] is not None and response_json['runtime'] > 0 else default_runtime,
            'season_number': response_json['season_number'],
            'tv_show_tmdb_id': series_id,
            'still_path': response_json['still_path'],
            'rating': response_json['vote_average'],
            #'vote_count': response_json['vote_count'],
            #'description': response_json.get('overview', ''),  
            'episode_type': response_json.get('episode_type', ''),
            'enabled': True,
        }
        episode_list.append(episode_info)
    else:
        # for each episode
        if 'episodes' not in response_json:
            return # should not happen

        for episode in response_json['episodes']:
            if default_runtime == None and episode['runtime'] is not None and episode['runtime'] > 0:
                default_runtime = episode['runtime']

            episode_info = {
                'tmdb_id': episode['id'],
                'episode_number': episode['episode_number'],
                'name': episode['name'][:255],
                'description': episode['overview'][:252] + "...",
                'runtime': episode['runtime'] if episode['runtime'] is not None and episode['runtime'] > 0 else default_runtime,
                'season_number': episode['season_number'],
                'tv_show_tmdb_id': episode['show_id'],
                'still_path': episode['still_path'],
                'rating': episode['vote_average'],
                #'vote_count': episode['vote_count'],
                #'description': episode.get('overview', '')[:255],  
                'episode_type': episode.get('episode_type', ''),
                'enabled': True,
            }
            episode_list.append(episode_info)

    #print("===== End of seasons =====")

    # create new episodes if they dont exist
    for episode in episode_list:
        episode_exists = Episodes.objects.filter(tmdb_id=episode['tmdb_id']).first()
        if episode_exists is None:
            # find the tv show
            tv_show = TVShows.objects.filter(tmdb_id=episode['tv_show_tmdb_id']).first()
            if tv_show is not None:
                episode['tv_show_id'] = tv_show
            elif load_single_tv_show_data_TMDB(episode['tv_show_tmdb_id']):
                # create tv show if it does not exist
                tv_show = TVShows.objects.filter(tmdb_id=episode['tv_show_tmdb_id']).first()
                episode['tv_show_id'] = tv_show

            # check if episode exists
            episode_exists = Episodes.objects.filter(tmdb_id=episode['tmdb_id'])
            if episode_exists == False:
                # create new episode
                new_episode = Episodes.objects.create(**episode)
        elif episode_exists and calculate_day_difference(episode_exists.last_updated.strftime('%Y-%m-%d'), 7):
            # update episode entry
            episode_exists.still_path = episode['still_path']
            episode_exists.name = episode['name']
            #episode_exists.vote_count = episode['vote_count']
            episode_exists.rating = episode['rating']
            episode_exists.description = episode['description']
            episode_exists.runtime = episode['runtime']
            episode_exists.save()

    # sort episodes from episode 1 down (ascending order)
    episode_list = sorted(episode_list, key=lambda x: x['episode_number'])
    
    return episode_list

# TODO: fetch popular tv shows from TMDB https://api.themoviedb.org/3/tv/popular
# TODO: fetch top rated tv shows from TMDB https://api.themoviedb.org/3/tv/top_rated


# get newly released tv shows from database cache
def fetch_tv_shows_new_releases_cached():
    new_releases_list = []

    tv_shows_new_releases = TVShowsNewReleases.objects.all()[:50]

    for item in tv_shows_new_releases:
        # populate tv show info
        #tv_show = TVShows.objects.filter(tmdb_id=item.tmdb_id).first()
        tv_show = TVShows.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
        if episodes.count() <= 0:
            # get episodes
            episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

        tv_show.episodes = episodes
        tv_show.type = "tv"
        new_releases_list.append(tv_show)

    return new_releases_list

# get tv shows trending daily from database cache
def fetch_tv_shows_trending_daily_cached():
    trending_daily_list = []

    tv_shows_trending_daily = TVShowsTrendingDaily.objects.all()[:50]

    for item in tv_shows_trending_daily:
        # populate tv show info
        tv_show = TVShows.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
        if episodes.count() <= 0:
            # get episodes
            episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

        tv_show.episodes = episodes
        tv_show.type = "tv"
        trending_daily_list.append(tv_show)

    return trending_daily_list

# get tv shows trending weekly from database cache
def fetch_tv_shows_trending_weekly_cached():
    trending_weekly_list = []

    tv_shows_trending_weekly = TVShowsTrendingWeekly.objects.all()[:50]

    for item in tv_shows_trending_weekly:
        # populate tv show info
        tv_show = TVShows.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
        if episodes.count() <= 0:
            # get episodes
            episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

        tv_show.episodes = episodes
        tv_show.type = "tv"
        trending_weekly_list.append(tv_show)

    return trending_weekly_list

# get tv shows trending netflix from database cache
def fetch_tv_shows_trending_netflix_cached():
    trending_netflix_list = []

    tv_shows_trending_netflix = TVShowsTrendingNetflix.objects.all()[:50]

    for item in tv_shows_trending_netflix:
        # populate tv show info
        tv_show = TVShows.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
        if episodes.count() <= 0:
            # get episodes
            episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

        tv_show.episodes = episodes
        tv_show.type = "tv"
        trending_netflix_list.append(tv_show)

    return trending_netflix_list

# get tv shows trending disney plus from database cache
def fetch_tv_shows_trending_disney_plus_cached():
    trending_disney_plus_list = []

    tv_shows_trending_disney_plus = TVShowsTrendingDisneyPlus.objects.all()[:50]

    for item in tv_shows_trending_disney_plus:
        # populate tv show info
        tv_show = TVShows.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
        if episodes.count() <= 0:
            # get episodes
            episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

        tv_show.episodes = episodes
        tv_show.type = "tv"
        trending_disney_plus_list.append(tv_show)

    return trending_disney_plus_list

# get tv shows trending amazon prime video from database cache
def fetch_tv_shows_trending_amazon_prime_cached():
    trending_amazon_prime_list = []

    tv_shows_trending_amazon_prime = TVShowsTrendingAmazonPrime.objects.all()[:50]

    for item in tv_shows_trending_amazon_prime:
        # populate tv show info
        tv_show = TVShows.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
        if episodes.count() <= 0:
            # get episodes
            episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

        tv_show.episodes = episodes
        tv_show.type = "tv"
        trending_amazon_prime_list.append(tv_show)

    return trending_amazon_prime_list

# get tv shows trending from all services trending from cache
def fetch_tv_shows_trending_services_cached():
    trending_netflix_list = []
    trending_disney_plus_list = []
    trending_amazon_prime_list = []

    tv_shows_trending_netflix = TVShowsTrendingNetflix.objects.all()[:50]
    tv_shows_trending_disney_plus = TVShowsTrendingDisneyPlus.objects.all()[:50]
    tv_shows_trending_amazon_prime = TVShowsTrendingAmazonPrime.objects.all()[:50]

    for item in tv_shows_trending_netflix:
        # populate tv show info
        tv_show = TVShows.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
        if episodes.count() <= 0:
            # get episodes
            episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

        tv_show.episodes = episodes
        tv_show.type = "tv"
        trending_netflix_list.append(tv_show)

    for item in tv_shows_trending_disney_plus:
        # populate tv show info
        tv_show = TVShows.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
        if episodes.count() <= 0:
            # get episodes
            episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

        tv_show.episodes = episodes
        tv_show.type = "tv"
        trending_disney_plus_list.append(tv_show)

    for item in tv_shows_trending_amazon_prime:
        # populate tv show info
        tv_show = TVShows.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        episodes = Episodes.objects.filter(tv_show_tmdb_id=tv_show.tmdb_id, season_number=1)
        if episodes.count() <= 0:
            # get episodes
            episodes = get_tv_season_episodes_TMDB(tv_show.tmdb_id, 1)

        tv_show.episodes = episodes
        tv_show.type = "tv"
        trending_amazon_prime_list.append(tv_show)

    data = {
        'netflix_tv_shows': trending_netflix_list,
        'disney_plus_tv_shows': trending_disney_plus_list,
        'amazon_prime_tv_shows': trending_amazon_prime_list
    }

    return data

# GET service specific trending shows
# PROVIDER                 | ID
#--------------------------#---------------
# netflix                  | 8
# netflix (ads)            | 1796
# disney+                  | 337
# amazon video             | 10
# amazon prime video       | 9 and 119
# amazon prime video (ads) | 2100
def fetch_tv_shows_trending_services(page_max=100):
    netflix_shows = []
    disney_plus_shows = []
    amazon_prime_shows = []

    # get all trending shows from TMDB
    all_trending_shows = fetch_tv_shows_trending_weekly_TMDB(page_max)

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
    }

    # for each show, get the streaming service it is available on
    for show in all_trending_shows:
        url = "https://api.themoviedb.org/3/tv/{series_id}/watch/providers"
        url = url.replace("{series_id}", str(show.tmdb_id))
        response = requests.get(url, headers=headers)
        response_json = response.json()

        if 'US' in response_json['results'] and 'flatrate' in response_json['results']['US']:
            providers = response_json['results']['US']['flatrate']
        elif 'CA' in response_json['results'] and 'flatrate' in response_json['results']['CA']:
            providers = response_json['results']['CA']['flatrate']
        elif 'US' in response_json['results'] and 'buy' in response_json['results']['US']:
            providers = response_json['results']['US']['buy']
        elif 'CA' in response_json['results'] and 'buy' in response_json['results']['CA']:
            providers = response_json['results']['CA']['buy']
        else:
            continue # skip

        # determine the streaming provider of the show
        for provider in providers:
            if provider['provider_id'] == (8 or 1796):
                # netflix
                if show not in netflix_shows:
                    netflix_shows.append(model_to_dict(show))
            elif provider['provider_id'] == 337:
                # disney+
                if show not in disney_plus_shows:
                    disney_plus_shows.append(model_to_dict(show))
            elif provider['provider_id'] == (9 or 10 or 119 or 2100):
                # amazon prime video
                if show not in amazon_prime_shows:
                    amazon_prime_shows.append(model_to_dict(show))

    # cache to database
    trending_netflix = TVShowsTrendingNetflix.objects.all()
    trending_disney_plus = TVShowsTrendingDisneyPlus.objects.all()
    trending_amazon_prime = TVShowsTrendingAmazonPrime.objects.all()

    for item in trending_netflix:
        if item.tmdb_id not in [tv_show['tmdb_id'] for tv_show in netflix_shows]:
            item.delete()

    for item in trending_disney_plus:
        if item.tmdb_id not in [tv_show['tmdb_id'] for tv_show in disney_plus_shows]:
            item.delete()

    for item in trending_amazon_prime:
        if item.tmdb_id not in [tv_show['tmdb_id'] for tv_show in amazon_prime_shows]:
            item.delete()

    for index, tv_show in enumerate(netflix_shows[:50]):
        if TVShowsTrendingNetflix.objects.filter(tmdb_id=tv_show['tmdb_id']).first() == None:
            # create new record
            data = {
                'tmdb_id': tv_show['tmdb_id'],
                'imdb_id': tv_show['imdb_id'],
                'rank': index + 1
            }
            TVShowsTrendingNetflix.objects.create(**data)

    for index, tv_show in enumerate(disney_plus_shows[:50]):
        if TVShowsTrendingDisneyPlus.objects.filter(tmdb_id=tv_show['tmdb_id']).first() == None:
            # create new record
            data = {
                'tmdb_id': tv_show['tmdb_id'],
                'imdb_id': tv_show['imdb_id'],
                'rank': index + 1
            }
            TVShowsTrendingDisneyPlus.objects.create(**data)

    for index, tv_show in enumerate(amazon_prime_shows[:50]):
        if TVShowsTrendingAmazonPrime.objects.filter(tmdb_id=tv_show['tmdb_id']).first() == None:
            # create new record
            data = {
                'tmdb_id': tv_show['tmdb_id'],
                'imdb_id': tv_show['imdb_id'],
                'rank': index + 1
            }
            TVShowsTrendingAmazonPrime.objects.create(**data)

    data = {
        'netflix_tv_shows': netflix_shows,
        'disney_plus_tv_shows': disney_plus_shows,
        'amazon_prime_tv_shows': amazon_prime_shows
    }

    return data


# get full genre info based on genre ids
def load_tv_show_genres(genres):
    all_genres = Genres.objects.all()  # Get the entire queryset

    genre_list = []

    for genre_id in genres:  # genres is a list of TMDB genre IDs
        genre_info = all_genres.filter(tmdb_id=genre_id).first()  # Correct lookup

        if genre_info is None:
            continue
        else:
            new_genre = {
                'tmdb_id': genre_id,  # Use genre_id directly
                'name': genre_info.name,
                'type': 1,
            }
            genre_list.append(new_genre)

    return genre_list
