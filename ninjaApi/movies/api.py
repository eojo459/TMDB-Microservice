import requests
from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from movies.models import Movies
from genres.api import Genre, GenreOut
from backendApi.utils.helper import calculate_day_difference
from genres.models import Genres
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
    run_time: int
    enabled: bool
    #expires: datetime

class MovieOutFull(Schema):
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
    #expires: datetime

################################
# API CONTROLLER METHODS
################################

### initial seeding ##
@router.get("/seeding/")
def movies_seeding(request):
    skip_round_1 = False
    skip_round_2 = True

    # get movies
    base_url = "https://api.themoviedb.org/3/discover/movie"
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
                        'title': result['title'][:255],
                        'rating': result['vote_average'],
                        'release_date': '9999-01-01' if result['release_date'] == '' else result['release_date'],
                        'description': result['overview'][:255],
                        'origin_location': '',
                        'languages': result['original_language'],
                        'imdb_link': '',
                        'last_updated': datetime.now().date(),
                        'run_time': 0,
                    }

                    # check if movie doesn't already exist
                    movie_exists = Movies.objects.filter(tmdb_id=result['id']).first()
                    if movie_exists and movie_exists.last_updated is not None:
                        if calculate_day_difference(movie_exists.last_updated.strftime('%Y-%m-%d'), 7):
                            # update movie entry
                            movie_exists.tmdb_id = result['id']
                            movie_exists.poster_url = result['poster_path']
                            movie_exists.title = result['title']
                            movie_exists.rating = result['rating']
                            movie_exists.release_date = result['release_date']
                            movie_exists.description = result['overview'][:255]
                            movie_exists.last_updated = datetime.now().date()
                            movie_exists.save()
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
                        'title': result['title'][:255],
                        'rating': result['vote_average'],
                        'release_date': '9999-01-01' if result['release_date'] == '' else result['release_date'],
                        'description': result['overview'][:255],
                        'origin_location': '',
                        'languages': result['original_language'],
                        'imdb_link': '',
                        'run_time': 0,
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
                            movie_exists.rating = result['rating']
                            movie_exists.release_date = result['release_date']
                            movie_exists.description = result['overview'][:255]
                            movie_exists.last_updated = datetime.now().date()
                            movie_exists.save()
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

    return {"success": True}
   #return response.json()

### initial data loading ##
@router.get("/seeding/data")
def movies_data_loading(request):
    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
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
        movie.status = response_json['status']

        # people credits
        credits = response_json['credits']

        # trailers
        trailers = response_json['videos']

        # genres
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
    
    return {"success": True}

# create new movie
@router.post("/", auth=None)
def create_movie(request, payload: Movie):
    movie = Movies.objects.create(**payload.dict())
    return {"id": movie.id}

# get movie by id
@router.get("/id/{id}", response=MovieOut)
def get_movie_by_id(request, id: str):
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
        return movie
    else:
        return {"Message": "Movie not found"}

# get movie by tmdb_id
@router.get("/tmdb_id/{tmdb_id}", response=MovieOut)
def get_movie_by_tmdb_id(request, tmdb_id: int):
    movie = get_object_or_404(Movies, tmdb_id=tmdb_id)
    return movie

# get movie by imdb_id
@router.get("/imdb_id/{imdb_id}", response=MovieOut)
def get_movie_by_imdb_id(request, imdb_id: str):
    movie = get_object_or_404(Movies, imdb_id=imdb_id)
    return movie

# list all movies
@router.get("/", response=List[MovieOut])
def list_all_movies(request):
    movies_list = Movies.objects.all()[:100]
    for movie in movies_list:
        if movie.imdb_id == None or movie.imdb_id == "":
            movie.imdb_id = "zz" + str(movie.tmdb_id)
        
        if movie.poster_url == None or movie.poster_url == "":
            movie.poster_url = ""
    return movies_list

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