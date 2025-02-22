from django.forms import model_to_dict
import requests
from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from movies.models import Movies, MoviesNewReleases, MoviesTrendingAmazonPrime, MoviesTrendingDaily, MoviesTrendingDisneyPlus, MoviesTrendingNetflix, MoviesTrendingWeekly
from genres.api import Genre, GenreOut
from backendApi.utils.helper import calculate_day_difference
from genres.models import Genres
from tvshows.api import TVShowOut
from tvshows.models import TVShows
from people.models import Peoples
from trailers.models import Trailers
from people.api import People, PeopleOut
from trailers.api import Trailer, TrailerOut
from decouple import config

router = Router()

################
# MODEL SCHEMAS
################
class Movie(Schema):
    tmdb_id: int
    imdb_id: str
    poster_url: str | None = None
    backdrop_url: str | None = None
    title: str
    rating: float | None = None
    release_date: date | str | None = None
    description: str
    origin_location: str
    languages: str
    imdb_link: str | None = None
    youtube_trailer: List[Trailer] = None
    actors_cast: List[People] = None
    director: List[People] = None
    genres: List[Genre] = None
    run_time: int | None = None
    enabled: bool
    expires: datetime | None = None

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

class MovieRecommendations(Schema):
    tmdb_id: int
    imdb_id: str | None = None
    poster_url: str | None = None
    backdrop_url: str | None = None
    title: str
    rating: float
    release_date: date | str | None = None
    description: str
    genres: List[Genre] | None = None
    languages: str
    media_type: str | None = None
    #run_time: int

class MovieOutFull(Schema):
    id: UUID | None = None
    tmdb_id: int | None = None
    imdb_id: str | None = None
    poster_url: str | None = None
    backdrop_url: str | None = None
    title: str | None = None
    rating: float | None = None
    release_date: date | str | None = None
    description: str | None = None
    origin_location: str | None = None
    languages: str | None = None
    imdb_link: str | None = None
    youtube_trailer: List[Trailer] = None
    actors_cast: List[People] = None
    director: List[People] = None
    genres: List[Genre] = None
    recommendations: List[MovieRecommendations] = None
    run_time: int | None = None
    enabled: bool | None = None
    media_type: str | None = None
    type: str = "movie"
    #expires: datetime

class TrendingServicesMovie(Schema):
    netflix_movies: List[MovieOutFull] | None = None
    amazon_prime_movies: List[MovieOutFull] | None = None
    disney_plus_movies: List[MovieOutFull] | None = None

################################
# API CONTROLLER METHODS
################################

### initial seeding ##
@router.get("/seeding/")
def movies_seeding(request):
    skip_round_1 = False
    skip_round_2 = False

    # TODO fetch data from other sources too
    fetch_movies_TMDB(skip_round_1, skip_round_2)
    return {"success": True}
   #return response.json()

### initial data loading ##
@router.get("/seeding/data")
def movies_data_loading(request):
    # TODO load data from other sources too
    load_movie_data_TMDB()
    return {"success": True}

# create new movie
@router.post("/", auth=None)
def create_movie(request, payload: Movie):
    movie = Movies.objects.create(**payload.dict())
    return {"id": movie.id}

# get movie by id
@router.get("/id/{id}", response=MovieOutFull)
def get_movie_by_id(request, id: str):
    movie_found = False
    try:
        # try regular uuid id
        movie = Movies.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(id=id).first()
        if movie is not None:
            movie_found = True
    except:
        # try imdb id
        try:
            movie = Movies.objects.prefetch_related(
                'youtube_trailer',
                'actors_cast',
                'director',
                'genres',
                'reviews'
            ).filter(imdb_id=id).first()
            if movie is not None:
                movie_found = True
        except:
            # try tmdb id
            try:
                movie = Movies.objects.prefetch_related(
                    'youtube_trailer',
                    'actors_cast',
                    'director',
                    'genres',
                    'reviews'
                ).filter(tmdb_id=id).first()
                if movie is not None:
                    movie_found = True
            except:
                return {"Message": "Movie not found"}
            
    if movie_found:
        movie.recommendations = get_movie_recommendations_logic_TMDB(movie.tmdb_id)
        return movie
    else:
        return {"Message": "Movie not found"}

# get movie by tmdb_id
@router.get("/tmdb_id/{tmdb_id}", response=MovieOutFull)
def get_movie_by_tmdb_id(request, tmdb_id: int):
    movie = Movies.objects.filter(tmdb_id=tmdb_id).first()
    if movie is None:
        # create new movie
        if load_single_movie_data_TMDB(tmdb_id):
            movie = Movies.objects.filter(tmdb_id=tmdb_id).first()
    
    # update movie if runtime == 0
    if movie.run_time <= 0:
        load_single_movie_data_TMDB(tmdb_id)
        movie = Movies.objects.filter(tmdb_id=tmdb_id).first()
    
    # get recommendations for movie
    movie.recommendations = get_movie_recommendations_logic_TMDB(movie.tmdb_id)

    return movie

# get movie by imdb_id
@router.get("/imdb_id/{imdb_id}", response=MovieOutFull)
def get_movie_by_imdb_id(request, imdb_id: str):
    movie = get_object_or_404(Movies, imdb_id=imdb_id)
    movie.recommendations = get_movie_recommendations_logic_TMDB(movie.tmdb_id)
    return movie

# get list of tv show by tmdb_id
@router.post("/tmdb_ids/", response=List[MovieOutFull])
def get_list_of_movies_by_tmdb_id(request, payload: List[object]):
    if request.method != 'POST':
        return 405, {"detail": "Method not allowed."}
    
    movies_list = []

    for item in payload:
        tmdb_id = item['tmdb_id']

        movie = Movies.objects.filter(tmdb_id=tmdb_id).first()
        if movie is None:
            # create new tv show
            if load_single_movie_data_TMDB(tmdb_id):
                tv_show = TVShows.objects.filter(tmdb_id=tmdb_id).first()

        # update tv show if seasons == 0
        if movie.run_time <= 0:
            load_single_movie_data_TMDB(tmdb_id)
            movie = Movies.objects.filter(tmdb_id=tmdb_id).first()


        #tv_show.recommendations = get_tv_recommendations_logic_TMDB(tmdb_id)
        movie.type = "movie"
        movies_list.append(movie)
    
    return movies_list

# list all movies first
@router.get("/", response=List[MovieOutFull])
def list_all_movies(request):
    movies_list = Movies.objects.prefetch_related(
        'youtube_trailer',
        'actors_cast',
        'director',
        'genres',
        'reviews'
    ).all()[:100]

    for movie in movies_list:
        #new_movie = model_to_dict(movie)
        if movie.imdb_id == None or movie.imdb_id == "":
            movie.imdb_id = "zz" + str(movie.tmdb_id)
        
        if movie.poster_url == None or movie.poster_url == "":
            movie.poster_url = ""

    return movies_list

# list all movies that contain a str in their title
@router.get("/title/{title_str}", response=List[MovieOutFull])
def get_movies_by_name(request, title_str: str):
    movies_list = Movies.objects.prefetch_related(
        'youtube_trailer',
        'actors_cast',
        'director',
        'genres',
        'reviews'
    ).filter(title__icontains=title_str)[:100]

    return movies_list

# list all movies and tv shows that contain a str in their title
@router.get("/all/title/{title_str}", response=List[MovieOutFull | TVShowOut])
def get_all_by_name(request, title_str: str):
    all_list = []

    movies_list = Movies.objects.prefetch_related(
        'youtube_trailer',
        'actors_cast',
        'director',
        'genres',
        'reviews'
    ).filter(title__icontains=title_str)[:100]

    for movie in movies_list:
        movie.media_type = "movie"
        all_list.append(movie)

    tv_show_list = TVShows.objects.prefetch_related(
        'youtube_trailer',
        'actors_cast',
        'director',
        'genres',
        'reviews'
    ).filter(title__icontains=title_str)[:100]

    for tv in tv_show_list:
        tv.media_type = "tv"
        all_list.append(tv)

    return all_list

# update movie by id
@router.put("/id/{id}")
def update_movie_by_id(request, id: str, payload: MovieOut):
    movie_found = False
    try:
        # try regular uuid id
        movie = Movies.objects.filter(id=id).first()
        if movie is not None:
            movie_found = True
    except:
        # try imdb id
        try:
            movie = Movies.objects.filter(imdb_id=id).first()
            if movie is not None:
                movie_found = True
        except:
            # try tmdb id
            try:
                movie = Movies.objects.filter(tmdb_id=id).first()
                if movie is not None:
                    movie_found = True
            except:
                return {"Message": "Movie not found"}
            
    if movie_found:
        for attr, value in payload.dict().items():
            setattr(movie, attr, value)
        movie.save()
        return {"success": True}
    else:
        return {"message": "Movie not found"}

# update movie by tmdb_id
@router.put("/tmdb_id/{tmdb_id}")
def update_movie_by_tmdb_id(request, tmdb_id: int, payload: MovieOut):
    movie = get_object_or_404(Movies, tmdb_id=tmdb_id)
    for attr, value in payload.dict().items():
        setattr(movie, attr, value)
    movie.save()
    return {"success": True}

# update movie by imdb_id
@router.put("/imdb_id/{imdb_id}")
def update_movie_by_imdb_id(request, imdb_id: str, payload: MovieOut):
    movie = get_object_or_404(Movies, imdb_id=imdb_id)
    for attr, value in payload.dict().items():
        setattr(movie, attr, value)
    movie.save()
    return {"success": True}

# delete/disable movie by id
@router.delete("/id/{id}")
def delete_movie_by_id(request, id: str):
    movie_found = False
    try:
        # try regular uuid id
        movie = Movies.objects.filter(id=id).first()
        if movie is not None:
            movie_found = True
    except:
        # try imdb id
        try:
            movie = Movies.objects.filter(imdb_id=id).first()
            if movie is not None:
                movie_found = True
        except:
            # try tmdb id
            try:
                movie = Movies.objects.filter(tmdb_id=id).first()
                if movie is not None:
                    movie_found = True
            except:
                return {"Message": "Movie not found"}
            
    if movie_found:
        #movie.delete()
        movie.enabled = False
        movie.archived = True
        movie.save()
        return {"success": True}
    else:
        return {"Message": "Movie not found"}

# delete/disable movie by tmdb_id
@router.delete("/tmdb_id/{tmdb_id}")
def delete_movie_by_tmdb_id(request, tmdb_id: int):
    movie = get_object_or_404(Movies, tmdb_id=tmdb_id)
    #movie.delete()
    movie.enabled = False
    movie.archived = True
    movie.save()
    return {"success": True}

# delete/disable movie by imdb_id
@router.delete("/imdb_id/{imdb_id}")
def delete_movie_by_imdb_id(request, imdb_id: str):
    movie = get_object_or_404(Movies, imdb_id=imdb_id)
    #movie.delete()
    movie.enabled = False
    movie.archived = True
    movie.save()
    return {"success": True}

# get all actors who belong to a movie
@router.get("/{movie_id}/credits/actors/", response=List[PeopleOut])
def get_movie_credits_actors(request, movie_id: str):
    movie_found = False
    try:
        # try regular uuid id
        movie = Movies.objects.filter(id=movie_id).first()
        if movie is not None:
            movie_found = True
    except:
        # try imdb id
        try:
            movie = Movies.objects.filter(imdb_id=movie_id).first()
            if movie is not None:
                movie_found = True
        except:
            # try tmdb id
            try:
                movie = Movies.objects.filter(tmdb_id=movie_id).first()
                if movie is not None:
                    movie_found = True
            except:
                return {"Message": "Movie not found"}
    
    if movie_found:
        # get actors for the movie
        actor_list = []
        actors = movie.actors_cast.all()
        for actor in actors:
            actor_info = Peoples.objects.filter(id=actor.id).first()
            if actor_info is not None and actor_info.avatar_path == None:
                actor_info.avatar_path = ""
                actor_list.append(actor_info)

        return actor_list
    else:
        return {"Message": "Movie not found"}

# get all directors who belong to a movie
@router.get("/{movie_id}/credits/directors/", response=List[PeopleOut])
def get_movie_credits_directors(request, movie_id: str):
    movie_found = False
    try:
        # try regular uuid id
        movie = Movies.objects.filter(id=movie_id).first()
        if movie is not None:
            movie_found = True
    except:
        # try imdb id
        try:
            movie = Movies.objects.filter(imdb_id=movie_id).first()
            if movie is not None:
                movie_found = True
        except:
            # try tmdb id
            try:
                movie = Movies.objects.filter(tmdb_id=movie_id).first()
                if movie is not None:
                    movie_found = True
            except:
                return {"Message": "Movie not found"}
            
    
    if movie_found:
        # get directors for the movie
        director_list = []
        directors = movie.director.all()
        for director in directors:
            director_info = Peoples.objects.filter(id=director.id).first()
            if director_info is not None and director_info.avatar_path == None:
                director_info.avatar_path = ""
                director_list.append(director_info)

        return director_list
    else:
        return {"Message": "Movie not found"}
    
# get all trailers for a movie
@router.get("/{movie_id}/trailers/", response=List[TrailerOut])
def get_movie_trailers(request, movie_id: str):
    movie_found = False
    try:
        # try regular uuid id
        movie = Movies.objects.filter(id=movie_id).first()
        if movie is not None:
            movie_found = True
    except:
        # try imdb id
        try:
            movie = Movies.objects.filter(imdb_id=movie_id).first()
            if movie is not None:
                movie_found = True
        except:
            # try tmdb id
            try:
                movie = Movies.objects.filter(tmdb_id=movie_id).first()
                if movie is not None:
                    movie_found = True
            except:
                return {"Message": "Movie not found"}
            
    if movie_found:
        # get trailers for the movie
        trailer_list = []
        trailers = movie.youtube_trailer.all()
        for trailer in trailers:
            trailer_info = Trailers.objects.filter(id=trailer.id).first()
            if trailer_info is not None:
                trailer_list.append(trailer_info)

        return trailer_list
    else:
        return {"Message": "Movie not found"}

# get all genres for a movie
@router.get("/{movie_id}/genres/", response=List[GenreOut])
def get_movie_genres(request, movie_id: str):
    movie_found = False
    try:
        # try regular uuid id
        movie = Movies.objects.filter(id=movie_id).first()
        if movie is not None:
            movie_found = True
    except:
        # try imdb id
        try:
            movie = Movies.objects.filter(imdb_id=movie_id).first()
            if movie is not None:
                movie_found = True
        except:
            # try tmdb id
            try:
                movie = Movies.objects.filter(tmdb_id=movie_id).first()
                if movie is not None:
                    movie_found = True
            except:
                return {"Message": "Movie not found"}
            
    if movie_found:
        # get genres for the movie
        genre_list = []
        genres = movie.genres.all()
        for genre in genres:
            genre_info = Genres.objects.filter(id=genre.id).first()
            if genre_info is not None:
                genre_list.append(genre_info)

        return genre_list
    else:
        return {"Message": "Movie not found"}
    
# get all recommendations/similiar movies for a movie
@router.get("/{tmdb_id}/recommended/", response=List[MovieOutFull])
def get_movie_recommendations(request, tmdb_id: str):
    # TODO: make this more robust and possibly use AI to get better recommendations
    movie_found = False

    # try tmdb id
    movie = Movies.objects.filter(tmdb_id=tmdb_id).first()
    if movie is not None:
        movie_found = True
            
    if movie_found == False:
        return {"Message": "Movie not found"}
    
    movies_list = get_movie_recommendations_logic_TMDB(tmdb_id)

    return movies_list

@router.get("/newly-released/", response=List[MovieOutFull])
def get_newly_released_movies_TMDB(request):
    #return fetch_movies_new_releases_TMDB()
    return fetch_movies_new_releases_cached()

@router.get("/trending/daily/", response=List[MovieOutFull])
def get_trending_movies_daily_TMDB(request):
    #return fetch_movies_trending_daily_TMDB()
    return fetch_movies_trending_daily_cached()

@router.get("/trending/weekly/", response=List[MovieOutFull])
def get_trending_movies_weekly_TMDB(request):
    #return fetch_movies_trending_weekly_TMDB()
    return fetch_movies_trending_weekly_cached()

@router.get("/details/{tmdb_id}", response=MovieOutFull)
def get_movie_details_TMDB(request, tmdb_id: str):
    return fetch_movie_by_TMDB_id(tmdb_id)

@router.get("/trending/streaming/", response=TrendingServicesMovie)
def get_trending_movies_streaming_services(request):
    #return fetch_movies_trending_services()
    return fetch_movies_trending_services_cached()

@router.get("/trending/netflix/", response=List[MovieOutFull])
def get_trending_movies_netflix(request):
    return fetch_movies_trending_netflix_cached()

@router.get("/trending/disney_plus/", response=List[MovieOutFull])
def get_trending_movies_disney_plus(request):
    return fetch_movies_trending_disney_plus_cached()

@router.get("/trending/amazon_prime/", response=List[MovieOutFull])
def get_trending_movies_amazon_prime(request):
    return fetch_movies_trending_amazon_prime_cached()

###################################
# HELPERS
###################################

# get recommendations for the movie specified
def get_movie_recommendations_logic_TMDB(movie_id):
    recommendation_list = []

    # get movies
    base_url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations"
    page = 1
    max_pages = 10 # TMDB limits us to 500 pages

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
    }

    print(f"===== Getting movie recommendations for {movie_id} =====")
    url = f"{base_url}?include_adult=false&language=en-US&page={page}&sort_by=popularity.desc"
    #url = f"{base_url}?include_adult=false&language=en-US&page={page}"

    response = requests.get(url, headers=headers)
    response_json = response.json()

    if response_json['total_pages'] >= 1:
        # get all the pages we can get
        while page <= max_pages:
            #print("===== Page " + str(page) + " =====")

            # for each result on this page, create new movie entry in database if doesn't already exist
            for result in response_json['results']:
                movie_info = {
                    'tmdb_id': result['id'],
                    #'imdb_id': "zz" + str(result['id']),
                    'poster_url': result['poster_path'],
                    'backdrop_url': result['backdrop_path'],
                    'title': result['title'][:255],
                    'rating': result['vote_average'],
                    'release_date': '9999-01-01' if result['release_date'] == '' else result['release_date'],
                    'description': result['overview'][:255],
                    'origin_location': '',
                    'languages': result['original_language'],
                    #'genres': result['genre_ids'],
                    #'last_updated': datetime.now().date(),
                    'run_time': 0,
                    #'media_type': result['media_type'],
                }

                movie_info = create_new_movie(movie_info)
                if movie_info is not None:
                    recommendation_list.append(movie_info)

            # go to next page
            page += 1
            url = f"{base_url}?include_adult=false&language=en-US&page={page}&sort_by=popularity.desc"
            #url = f"{base_url}?include_adult=false&language=en-US&page={page}"
            response = requests.get(url, headers=headers)
            response_json = response.json()

    print("===== End of movie recommendations =====")
    
    return recommendation_list


# get movies from TMDB
def fetch_movies_TMDB(skip_round_1=False, skip_round_2=True):
    base_url = "https://api.themoviedb.org/3/discover/movie"
    page = 1
    max_pages = 500 # TMDB limits us to 500 pages

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
    }

    # round 1
    # 1st round get based on most popular sort by descending (highest popularity to least popularity) 
    if skip_round_1 is False:
        print("===== Starting round 1 =====")
        url = f"{base_url}?include_adult=false&language=en-US&page={page}&sort_by=popularity.desc"

        response = requests.get(url, headers=headers)
        response_json = response.json()

        if response_json['total_pages'] > 1:
            # get all the pages we can get
            while page <= max_pages:
                print("===== Page " + str(page) + " =====")

                # for each result on this page, create new movie entry in database if doesn't already exist
                for result in response_json['results']:
                    movie_info = {
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
                        #'run_time': result["runtime"],
                    }

                    # check if movie doesn't already exist
                    movie_exists = Movies.objects.filter(tmdb_id=result['id']).first()
                    if movie_exists and movie_exists.last_updated is not None:
                        if calculate_day_difference(movie_exists.last_updated.strftime('%Y-%m-%d'), 7):
                            # update movie entry
                            movie_exists.tmdb_id = result['id']
                            movie_exists.poster_url = result['poster_path']
                            movie_exists.title = result['title']
                            movie_exists.rating = result['vote_average']
                            movie_exists.release_date = result['release_date']
                            movie_exists.description = result['overview'][:255]
                            #movie_exists.run_time = result['runtime']
                            movie_exists.last_updated = datetime.now().date()
                            movie_exists.save()
                    # elif movie_exists and movie_exists.run_time <= 0:
                    #     # update movie entry
                    #     movie_exists.run_time = result['runtime']
                    #     movie_exists.save()
                    elif movie_exists is None:
                        # create new movie entry
                        Movies.objects.create(**movie_info)
                    else:
                        continue # skip

                # go to next page
                page += 1
                url = f"{base_url}?include_adult=false&language=en-US&page={page}&sort_by=popularity.desc"
                response = requests.get(url, headers=headers)
                response_json = response.json()

        print("===== End of round 1 =====")

    # round 2
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

                # for each result on this page, create new movie entry in database if doesn't already exist
                for result in response_json['results']:
                    movie_info = {
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
                        #'run_time': result["runtime"],
                        'last_updated': datetime.now().date(),
                    }

                    # check if movie doesn't already exist
                    movie_exists = Movies.objects.filter(tmdb_id=result['id']).first()
                    if movie_exists and movie_exists.last_updated is not None:
                        if calculate_day_difference(movie_exists.last_updated.strftime('%Y-%m-%d'), 7):
                            # update movie entry
                            movie_exists.tmdb_id = result['id']
                            movie_exists.poster_url = result['poster_path']
                            movie_exists.title = result['title']
                            movie_exists.rating = result['vote_average']
                            movie_exists.release_date = result['release_date']
                            movie_exists.description = result['overview'][:255]
                            movie_exists.last_updated = datetime.now().date()
                            movie_exists.save()
                    # elif movie_exists and movie_exists.run_time <= 0:
                    #     # update movie entry
                    #     movie_exists.run_time = result['runtime']
                    #     movie_exists.save()
                    elif movie_exists is None:
                        # create new movie entry
                        Movies.objects.create(**movie_info)
                    else:
                        continue # skip

                # go to next page
                page += 1
                url = f"{base_url}?include_adult=false&language=en-US&primary_release_date.gte={release_date_min}&primary_release_date.lte={release_date_max}&page={page}&sort_by=primary_release_date.desc"
                response = requests.get(url, headers=headers)
                response_json = response.json()

    return True

# get newly released movies from TMDB
def fetch_movies_new_releases_TMDB():
    base_url = "https://api.themoviedb.org/3/movie/now_playing"
    page = 1
    max_pages = 10 # TMDB limits us to 500 pages
    movie_list = []

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
    }

    # get based on newly released, popular sort by descending (highest popularity to least popularity) 

    print("===== Fetching newly released movies =====")
    url = f"{base_url}?include_adult=false&language=en-US&page={page}"

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
                movie_exists = Movies.objects.prefetch_related(
                    'youtube_trailer',
                    'actors_cast',
                    'director',
                    'genres',
                    'reviews'
                ).filter(tmdb_id=result['id']).first()
                if movie_exists and movie_exists.last_updated is not None:
                    if calculate_day_difference(movie_exists.last_updated.strftime('%Y-%m-%d'), 7):
                        # update movie entry
                        movie_exists.tmdb_id = result['id']
                        movie_exists.poster_url = result['poster_path']
                        movie_exists.title = result['title']
                        movie_exists.rating = result['vote_average']
                        movie_exists.release_date = '9999-01-01' if result['release_date'] == '' else result['release_date'],
                        movie_exists.release_date = movie_exists.release_date[0]
                        movie_exists.description = result['overview'][:255]
                        #movie_exists.run_time = result['runtime']
                        #movie_exists.last_updated = str(datetime.now().date())
                        movie_exists.save()

                    movie_list.append(movie_exists)
                elif movie_exists is None:
                    # create new movie entry
                    movie = Movies.objects.create(**movie_info)
                    
                    # assign genres
                    genres = Genres.objects.filter(tmdb_id__in=result['genre_ids'])
                    movie.genres.set(genres)

                    # assign trailers
                    #movie.youtube_trailer.set()

                    movie.save()

                    load_single_movie_data_TMDB(movie.tmdb_id)
                    movie_full = Movies.objects.prefetch_related(
                        'youtube_trailer',
                        'actors_cast',
                        'director',
                        'genres',
                        'reviews'
                    ).filter(tmdb_id=movie.tmdb_id).first()

                    if movie_full is not None:
                        movie_list.append(movie_full)
                else:
                    continue # skip

            # go to next page
            page += 1
            url = f"{base_url}?include_adult=false&language=en-US&page={page}"
            response = requests.get(url, headers=headers)
            response_json = response.json()

        print("===== End of newly released movies =====")

    # update new releases movies cache
    movies_new_releases = MoviesNewReleases.objects.all()
    for item in movies_new_releases:
        if item.tmdb_id not in [movie.tmdb_id for movie in movie_list]:
            item.delete()

    for index, movie in enumerate(movie_list[:50]):
        if MoviesNewReleases.objects.filter(tmdb_id=movie.tmdb_id).first() == None:
            # create new release
            data = {
                'tmdb_id': movie.tmdb_id,
                'imdb_id': movie.imdb_id,
                'rank': index + 1
            }
            MoviesNewReleases.objects.create(**data)

    return movie_list

# fetch trending now movies from TMDB (weekly trending)
def fetch_movies_trending_weekly_TMDB(page_max=10):
    base_url = "https://api.themoviedb.org/3/trending/movie/week"
    page = 1
    max_pages = page_max # TMDB limits us to 500 pages
    movies_list = []

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
    }

    print("===== Fetching trending weekly movies =====")
    url = f"{base_url}?include_adult=false&language=en-US&page={page}"

    response = requests.get(url, headers=headers)
    response_json = response.json()

    if response_json['total_pages'] > 1:
        # get all the pages we can get
        while page <= max_pages:
            print("===== Page " + str(page) + " =====")

            # for each result on this page, create new movie entry in database if doesn't already exist
            for result in response_json['results']:
                movie_info = {
                    'tmdb_id': result['id'],
                    'imdb_id': "zz" + str(result['id']),
                    'poster_url': result['poster_path'],
                    'backdrop_url': result['backdrop_path'],
                    'title': result['title'][:255],
                    'rating': result['vote_average'],
                    'release_date': '0001-01-01' if result['release_date'] == '' else result['release_date'],
                    'description': result['overview'][:255],
                    'origin_location': '',
                    'languages': result['original_language'],
                    'imdb_link': '',
                    'last_updated': datetime.now().date(),
                }

                # check if movie doesn't already exist
                movie_exists = Movies.objects.prefetch_related(
                    'youtube_trailer',
                    'actors_cast',
                    'director',
                    'genres',
                    'reviews'
                ).filter(tmdb_id=result['id']).first()
                if movie_exists and movie_exists.last_updated is not None:
                    if calculate_day_difference(movie_exists.last_updated.strftime('%Y-%m-%d'), 7):
                        # update movie entry
                        movie_exists.tmdb_id = result['id']
                        movie_exists.poster_url = result['poster_path']
                        movie_exists.title = result['title']
                        movie_exists.rating = result['vote_average']
                        movie_exists.release_date = '0001-01-01' if result['release_date'] == '' else result['release_date'],
                        movie_exists.release_date = movie_exists.release_date[0]
                        movie_exists.description = result['overview'][:255]
                        movie_exists.last_updated = str(datetime.now().date())
                        movie_exists.save()

                    movies_list.append(movie_exists)
                elif movie_exists is None:
                    # create new movie entry
                    movie = Movies.objects.create(**movie_info)

                    # assign genres
                    genres = Genres.objects.filter(tmdb_id__in=result['genre_ids'])
                    movie.genres.set(genres)
                    movie.save()

                    load_single_movie_data_TMDB(movie.tmdb_id)
                    movie_full = Movies.objects.prefetch_related(
                        'youtube_trailer',
                        'actors_cast',
                        'director',
                        'genres',
                        'reviews'
                    ).filter(tmdb_id=movie.tmdb_id).first()

                    if movie_full is not None:
                        movies_list.append(movie_full)
                else:
                    continue # skip

            # go to next page
            page += 1
            url = f"{base_url}?include_adult=false&language=en-US&page={page}"
            response = requests.get(url, headers=headers)
            response_json = response.json()

        print("===== End of trending weekly movies =====")
    
    # update trending weekly movies cache
    movies_trending_weekly = MoviesTrendingWeekly.objects.all()
    for item in movies_trending_weekly:
        if item.tmdb_id not in [movie.tmdb_id for movie in movies_list]:
            item.delete()

    for index, movie in enumerate(movies_list[:50]):
        if MoviesTrendingWeekly.objects.filter(tmdb_id=movie.tmdb_id).first() == None:
            # create trending weekly movie
            data = {
                'tmdb_id': movie.tmdb_id,
                'imdb_id': movie.imdb_id,
                'rank': index + 1
            }
            MoviesTrendingWeekly.objects.create(**data)

    return movies_list

# fetch top picks today movies from TMDB (today's trending)
def fetch_movies_trending_daily_TMDB():
    base_url = "https://api.themoviedb.org/3/trending/movie/day"
    page = 1
    max_pages = 10 # TMDB limits us to 500 pages
    movies_list = []

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
    }

    print("===== Fetching trending daily movies =====")
    url = f"{base_url}?include_adult=false&language=en-US&page={page}"

    response = requests.get(url, headers=headers)
    response_json = response.json()

    if response_json['total_pages'] > 1:
        # get all the pages we can get
        while page <= max_pages:
            print("===== Page " + str(page) + " =====")

            # for each result on this page, create new movie entry in database if doesn't already exist
            for result in response_json['results']:
                movie_info = {
                    'tmdb_id': result['id'],
                    'imdb_id': "zz" + str(result['id']),
                    'poster_url': result['poster_path'],
                    'backdrop_url': result['backdrop_path'],
                    'title': result['title'][:255],
                    'rating': result['vote_average'],
                    'release_date': '0001-01-01' if result['release_date'] == '' else result['release_date'],
                    'description': result['overview'][:255],
                    'origin_location': '',
                    'languages': result['original_language'],
                    'imdb_link': '',
                    'last_updated': datetime.now().date(),
                    'enabled': True,
                }

                # check if movie doesn't already exist
                movie_exists = Movies.objects.prefetch_related(
                    'youtube_trailer',
                    'actors_cast',
                    'director',
                    'genres',
                    'reviews'
                ).filter(tmdb_id=result['id']).first()
                if movie_exists and movie_exists.last_updated is not None:
                    if calculate_day_difference(movie_exists.last_updated.strftime('%Y-%m-%d'), 7):
                        # update movie entry
                        movie_exists.tmdb_id = result['id']
                        movie_exists.poster_url = result['poster_path']
                        movie_exists.title = result['title']
                        movie_exists.rating = result['vote_average']
                        movie_exists.release_date = '0001-01-01' if result['release_date'] == '' else result['release_date'],
                        movie_exists.release_date = movie_exists.release_date[0]
                        movie_exists.description = result['overview'][:255]
                        movie_exists.last_updated = datetime.now().date()
                        movie_exists.save()

                    movies_list.append(movie_exists)
                elif movie_exists is None:
                    # create new movie entry
                    movie = Movies.objects.create(**movie_info)

                    # assign genres
                    genres = Genres.objects.filter(tmdb_id__in=result['genre_ids'])
                    movie.genres.set(genres)
                    movie.save()

                    load_single_movie_data_TMDB(movie.tmdb_id)
                    movie_full = Movies.objects.prefetch_related(
                        'youtube_trailer',
                        'actors_cast',
                        'director',
                        'genres',
                        'reviews'
                    ).filter(tmdb_id=movie.tmdb_id).first()

                    if movie_full is not None:
                        movies_list.append(movie_full)
                else:
                    continue # skip

            # go to next page
            page += 1
            url = f"{base_url}?include_adult=false&language=en-US&page={page}"
            response = requests.get(url, headers=headers)
            response_json = response.json()

        print("===== End of trending daily movies =====")

    # update trending daily movies cache
    movies_trending_daily = MoviesTrendingDaily.objects.all()
    for item in movies_trending_daily:
        if item.tmdb_id not in [movie.tmdb_id for movie in movies_list]:
            item.delete()

    for index, movie in enumerate(movies_list[:50]):
        if MoviesTrendingDaily.objects.filter(tmdb_id=movie.tmdb_id).first() == None:
            # create trending daily movie
            data = {
                'tmdb_id': movie.tmdb_id,
                'imdb_id': movie.imdb_id,
                'rank': index + 1
            }
            MoviesTrendingDaily.objects.create(**data)

    return movies_list

# fetch Laugh Out Loud Comedies (Comedy, Family, Romantic Comedy)
# fetch Mind-Bending Sci-Fi Journeys (Science Fiction, Fantasy, Adventure)
# fetch True Stories That Inspire (Documentary, Biographical, Historical)
# fetch Epic Adventures Await (Action, Adventure, Fantasy)
# fetch Edge of Your Seat (Action, Adventure, Thriller)
# fetch Animated Adventures (Animation, Family, Fantasy)
# fetch Thrills and Chills: Horror Nights (Horror, Thriller, Supernatural)
# fetch Haunting Ghost Stories (Horror, Supernatural, Thriller)
# fetch Feel-Good Flicks (Comedy, Drama, Family)

# get movies from TMDB
def fetch_movie_by_TMDB_id(movie_id):
    base_url = "https://api.themoviedb.org/3/movie/" + movie_id

    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
    }

    print(f"===== fetching data for {movie_id} =====")
    url = base_url

    response = requests.get(url, headers=headers)
    response_json = response.json()

    # for each result on this page, create new movie entry in database if doesn't already exist

    movie_info = {
        'tmdb_id': response_json['id'],
        'imdb_id': response_json['imdb_id'],
        'poster_url': response_json['poster_path'],
        'backdrop_url': response_json['backdrop_path'],
        'title': response_json['title'][:255],
        'rating': response_json['vote_average'],
        'release_date': '9999-01-01' if response_json['release_date'] == '' else response_json['release_date'],
        'description': response_json['overview'][:255],
        'origin_location': '',
        'languages': response_json['original_language'],
        'imdb_link': '',
        'last_updated': datetime.now().date(),
        'run_time': response_json["runtime"],
        'status': response_json["status"],
    }

    # check if movie doesn't already exist
    movie_exists = Movies.objects.filter(tmdb_id=response_json['id']).first()
    if movie_exists and movie_exists.last_updated is not None:
        if calculate_day_difference(movie_exists.last_updated.strftime('%Y-%m-%d'), 7):
            # update movie entry
            movie_exists.tmdb_id = response_json['id']
            movie_exists.poster_url = response_json['poster_path']
            movie_exists.title = response_json['title']
            movie_exists.rating = response_json['vote_average']
            movie_exists.release_date = response_json['release_date']
            movie_exists.description = response_json['overview'][:255]
            #movie_exists.run_time = response_json['runtime']
            movie_exists.last_updated = datetime.now().date()
            movie_exists.save()
            return movie_exists
    elif movie_exists and movie_exists.run_time <= 0:
        # update movie entry
        movie_exists.run_time = response_json['runtime']
        movie_exists.save()
        return movie_exists
    elif movie_exists is None:
        # create new movie entry
        movie = Movies.objects.create(**movie_info)

        # assign genres
        genres = Genres.objects.filter(tmdb_id__in=response_json['genre_ids'])
        movie.genres.set(genres)
        movie.save()

        load_single_movie_data_TMDB(movie.tmdb_id)
        movie_full = Movies.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=movie.tmdb_id).first()

        if movie_full is not None:
            return movie_full

# get the details for each movie from TMDB
def load_movie_data_TMDB():
    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
    }
    
    # get all movies
    movies = Movies.objects.all()

    print("===== Starting movie detail setup =====")
    movie_count = 1

    for movie in movies:
        print(f"===== Movie #{movie_count}: {movie.title}")
        actor_list = []
        director_list = []
        genre_list = []
        trailer_list = []

        # url to get the details about a movie
        url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}?language=en-US&append_to_response=videos,images,credits"
        response = requests.get(url, headers=headers)
        response_json = response.json()

        # update imdb_id
        if movie.imdb_id is not None and movie.imdb_id != '':
            if movie.imdb_id == int(movie.imdb_id[2:]):
                movie.imdb_id = response_json['imdb_id']

        # update status
        if "status" in response_json:
            movie.status = response_json['status']

        # update runtime
        if "runtime" in response_json and movie.run_time <= 0:
            movie.run_time = response_json['runtime'] 

        # update backdrop
        if "backdrop_path" in response_json and movie.backdrop_url is None:
            movie.backdrop_url = response_json['backdrop_path']

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
        
        # foreach movie get the trailers
        for trailer in trailers['results']:
            existing_trailer = Trailers.objects.filter(video_id=trailer['id']).first()
            if existing_trailer is not None:
                # check if we already have a many to many relationship with this trailer for the movie
                trailer_exists = movie.youtube_trailer.filter(id=existing_trailer.id).exists()
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
            movie.actors_cast.set(actor_list)

        if len(director_list) > 0:
            movie.director.set(director_list)

        if len(trailer_list) > 0:
            movie.youtube_trailer.set(trailer_list)

        if len(genre_list) > 0:
            movie.genres.set(genre_list)

        movie.save()
        movie_count += 1

    return True

def create_new_movie(movie_info):
    # check if movie doesn't already exist
    movie_exists = Movies.objects.prefetch_related(
        'youtube_trailer',
        'actors_cast',
        'director',
        'genres',
        'reviews'
    ).filter(tmdb_id=movie_info['tmdb_id']).first()
    if movie_exists and movie_exists.last_updated is not None:
        if calculate_day_difference(movie_exists.last_updated.strftime('%Y-%m-%d'), 7):
            # update movie entry
            movie_exists.tmdb_id = movie_info['tmdb_id']
            movie_exists.poster_url = movie_info['poster_url']
            movie_exists.title = movie_info['title']
            movie_exists.rating = movie_info['rating']
            movie_exists.release_date = movie_info['release_date']
            movie_exists.description = movie_info['description'][:255]
            #movie_exists.run_time = result['runtime']
            movie_exists.last_updated = datetime.now().date()
            movie_exists.save()
            return movie_exists
    elif movie_exists:
        return movie_exists
    elif movie_exists is None:
        # create new movie entry
        new_movie = Movies.objects.create(**movie_info)
        new_movie_full = Movies.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=movie_info['tmdb_id']).first() 
        return new_movie_full
    
# get the details for a movie from TMDB
def load_single_movie_data_TMDB(tmdb_id):
    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
    }
    
    # get all movies
    movie = Movies.objects.filter(tmdb_id=tmdb_id).first()
    if movie is None:
        return False

    actor_list = []
    director_list = []
    genre_list = []
    trailer_list = []

    # url to get the details about a movie
    url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}?language=en-US&append_to_response=videos,images,credits"
    response = requests.get(url, headers=headers)
    response_json = response.json()

    # update imdb_id
    if movie.imdb_id is not None and movie.imdb_id != '':
        if movie.imdb_id == int(movie.imdb_id[2:]):
            movie.imdb_id = response_json['imdb_id']

    # update status
    if "status" in response_json:
        movie.status = response_json['status']

    # update runtime
    if "runtime" in response_json and movie.run_time <= 0:
        movie.run_time = response_json['runtime'] 

    # update backdrop
    if "backdrop_path" in response_json and movie.backdrop_url is None:
        movie.backdrop_url = response_json['backdrop_path']

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
    
    # foreach movie get the trailers
    for trailer in trailers['results']:
        existing_trailer = Trailers.objects.filter(video_id=trailer['id']).first()
        if existing_trailer is not None:
            # check if we already have a many to many relationship with this trailer for the movie
            trailer_exists = movie.youtube_trailer.filter(id=existing_trailer.id).exists()
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
        movie.actors_cast.set(actor_list)

    if len(director_list) > 0:
        movie.director.set(director_list)

    if len(trailer_list) > 0:
        movie.youtube_trailer.set(trailer_list)

    if len(genre_list) > 0:
        movie.genres.set(genre_list)

    movie.save()

    return True

# get newly released movies from database cache
def fetch_movies_new_releases_cached():
    new_releases_list = []

    movies_new_releases = MoviesNewReleases.objects.all()[:50]

    for item in movies_new_releases:
        # populate movie info
        movie = Movies.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        new_releases_list.append(movie)

    return new_releases_list

# get trending daily movies from database cache
def fetch_movies_trending_daily_cached():
    trending_daily_list = []

    movies_trending_daily = MoviesTrendingDaily.objects.all()[:50]

    for item in movies_trending_daily:
        # populate movie info
        movie = Movies.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        trending_daily_list.append(movie)

    return trending_daily_list

# get trending weekly movies from database cache
def fetch_movies_trending_weekly_cached():
    trending_weekly_list = []

    movies_trending_weekly = MoviesTrendingWeekly.objects.all()[:50]

    for item in movies_trending_weekly:
        # populate movie info
        movie = Movies.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        trending_weekly_list.append(movie)

    return trending_weekly_list

# get movies trending netflix from database cache
def fetch_movies_trending_netflix_cached():
    trending_netflix_list = []

    movies_trending_netflix = MoviesTrendingNetflix.objects.all()[:50]

    for item in movies_trending_netflix:
        # populate tv show info
        movie = Movies.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        movie.type = "movie"
        trending_netflix_list.append(movie)
        
    return trending_netflix_list

# get movies trending disney plus from database cache
def fetch_movies_trending_disney_plus_cached():
    trending_disney_plus_list = []

    movies_trending_disney_plus = MoviesTrendingDisneyPlus.objects.all()[:50]

    for item in movies_trending_disney_plus:
        # populate tv show info
        movie = Movies.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        movie.type = "movie"
        trending_disney_plus_list.append(movie)

    return trending_disney_plus_list

# get movies trending amazon prime video from database cache
def fetch_movies_trending_amazon_prime_cached():
    trending_amazon_prime_list = []

    movies_trending_amazon_prime = MoviesTrendingAmazonPrime.objects.all()[:50]

    for item in movies_trending_amazon_prime:
        # populate tv show info
        movie = Movies.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        movie.type = "movie"
        trending_amazon_prime_list.append(movie)

    return trending_amazon_prime_list

# get movies trending from all services trending from cache
def fetch_movies_trending_services_cached():
    trending_netflix_list = []
    trending_disney_plus_list = []
    trending_amazon_prime_list = []

    movies_trending_netflix = MoviesTrendingNetflix.objects.all()[:50]
    movies_trending_disney_plus = MoviesTrendingDisneyPlus.objects.all()[:50]
    movies_trending_amazon_prime = MoviesTrendingAmazonPrime.objects.all()[:50]

    for item in movies_trending_netflix:
        # populate tv show info
        movie = Movies.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        movie.type = "movie"
        trending_netflix_list.append(movie)

    for item in movies_trending_disney_plus:
        # populate tv show info
        movie = Movies.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        movie.type = "movie"
        trending_disney_plus_list.append(movie)

    for item in movies_trending_amazon_prime:
        # populate tv show info
        movie = Movies.objects.prefetch_related(
            'youtube_trailer',
            'actors_cast',
            'director',
            'genres',
            'reviews'
        ).filter(tmdb_id=item.tmdb_id).first()
        movie.type = "movie"
        trending_amazon_prime_list.append(movie)

    data = {
        'netflix_movies': trending_netflix_list,
        'disney_plus_movies': trending_disney_plus_list,
        'amazon_prime_movies': trending_amazon_prime_list
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
def fetch_movies_trending_services(max_pages=100):
    netflix_movies = []
    disney_plus_movies = []
    amazon_prime_movies = []

    # get all trending movies from TMDB
    all_trending_movies = fetch_movies_trending_weekly_TMDB(max_pages)

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config('TMDB_API_TOKEN'),
    }

    # for each movie, get the streaming service it is available on
    for movie in all_trending_movies:
        url = "https://api.themoviedb.org/3/movie/{series_id}/watch/providers"
        url = url.replace("{series_id}", str(movie.tmdb_id))
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

        # determine the streaming provider of the movie
        for provider in providers:
            if provider['provider_id'] == (8 or 1796):
                # netflix
                if movie not in netflix_movies:
                    netflix_movies.append(model_to_dict(movie))
            elif provider['provider_id'] == 337:
                # disney+
                if movie not in disney_plus_movies:
                    disney_plus_movies.append(model_to_dict(movie))
            elif provider['provider_id'] == (9 or 10 or 119 or 2100):
                # amazon prime video
                if movie not in amazon_prime_movies:
                    amazon_prime_movies.append(model_to_dict(movie))

    # cache to database
    trending_netflix = MoviesTrendingNetflix.objects.all()
    trending_disney_plus = MoviesTrendingDisneyPlus.objects.all()
    trending_amazon_prime = MoviesTrendingAmazonPrime.objects.all()

    for item in trending_netflix:
        if item.tmdb_id not in [movie['tmdb_id'] for movie in netflix_movies]:
            item.delete()

    for item in trending_disney_plus:
        if item.tmdb_id not in [movie['tmdb_id'] for movie in disney_plus_movies]:
            item.delete()

    for item in trending_amazon_prime:
        if item.tmdb_id not in [movie['tmdb_id'] for movie in amazon_prime_movies]:
            item.delete()

    for index, movie in enumerate(netflix_movies[:50]):
        if MoviesTrendingNetflix.objects.filter(tmdb_id=movie['tmdb_id']).first() == None:
            # create new record
            data = {
                'tmdb_id': movie['tmdb_id'],
                'imdb_id': movie['imdb_id'],
                'rank': index + 1
            }
            MoviesTrendingNetflix.objects.create(**data)

    for index, movie in enumerate(disney_plus_movies[:50]):
        if MoviesTrendingDisneyPlus.objects.filter(tmdb_id=movie['tmdb_id']).first() == None:
            # create new record
            data = {
                'tmdb_id': movie['tmdb_id'],
                'imdb_id': movie['imdb_id'],
                'rank': index + 1
            }
            MoviesTrendingDisneyPlus.objects.create(**data)

    for index, movie in enumerate(amazon_prime_movies[:50]):
        if MoviesTrendingAmazonPrime.objects.filter(tmdb_id=movie['tmdb_id']).first() == None:
            # create new record
            data = {
                'tmdb_id': movie['tmdb_id'],
                'imdb_id': movie['imdb_id'],
                'rank': index + 1
            }
            MoviesTrendingAmazonPrime.objects.create(**data)

    data = {
        'netflix_movies': netflix_movies,
        'disney_plus_movies': disney_plus_movies,
        'amazon_prime_movies': amazon_prime_movies
    }

    return data