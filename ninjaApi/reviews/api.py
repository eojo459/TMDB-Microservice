from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
import requests
from movies.models import Movies
from trailers.models import Trailers
from tvshows.models import TVShows
from reviews.models import Reviews
from decouple import config

router = Router()

################
# MODEL SCHEMAS
################
class Review(Schema):
    imdb_id: str
    name: str
    username: str
    avatar_path: str | None = None
    rating: int | None = None
    content: str
    created_at: datetime
    updated_at: datetime
    review_id: str
    imdb_review_url: str

class ReviewOut(Schema):
    id: UUID
    imdb_id: str
    name: str
    username: str
    avatar_path: str | None = None
    rating: int | None = None
    content: str
    created_at: datetime
    updated_at: datetime
    review_id: str
    imdb_review_url: str

################################
# API CONTROLLER METHODS
################################

### initial seeding ##
@router.get("/seeding/")
def reviews_seeding(request):
    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    page = 1
    max_pages = 500
    total_pages = 0

    print("===== Reviews seeding started =====")
    movie_count = 1

    # get all movies
    movies = Movies.objects.all()
    for movie in movies:
        print(f"===== Movie #{movie_count}: {movie.title}")
        
        # reviews for movies
        movie_reviews_base_url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}/reviews?page={page}"

        # get movie reviews
        movies_response = requests.get(movie_reviews_base_url, headers=headers)
        movies_response_json = movies_response.json()

        total_pages = movies_response_json['total_pages']
        if total_pages >= 1:
            # get all the pages we can get
            while page <= max_pages and page <= total_pages:
                for review in movies_response_json['results']:
                    review_exists = Reviews.objects.filter(imdb_id=review['id']).first()
                    if review_exists is None:
                        # create new review in database
                        new_review = {
                            'imdb_id': review['id'],
                            'name': review['author'],
                            'username': review['author_details']['username'],
                            'avatar_path': review['author_details']['avatar_path'],
                            'rating': review['author_details']['rating'],
                            'content': review['content'][:255],
                            'created_at': review['created_at'],
                            'updated_at': review['updated_at'],
                            'imdb_review_url': review['url'],
                        }
                        Reviews.objects.create(**new_review)

                # go to next page
                page += 1
                url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}/reviews?page={page}"
                response = requests.get(url, headers=headers)
                movies_response_json = response.json()

        movie_count += 1

    page = 1
    tvshow_count = 1

    # get all tv shows
    tvshows = TVShows.objects.all()
    for tvshow in tvshows:
        print(f"===== TV Show #{tvshow_count}: {tvshow.title}")

        # reviews for tv shows
        tvshow_reviews_base_url = f"https://api.themoviedb.org/3/tv/{tvshow.tmdb_id}/reviews?page={page}"

        # get tv shows reviews
        tvshow_response = requests.get(tvshow_reviews_base_url, headers=headers)
        tvshow_response_json = tvshow_response.json()

        total_pages = tvshow_response_json['total_pages']
        if total_pages >= 1:
            # get all the pages we can get
            while page <= max_pages and page <= total_pages:
                for review in tvshow_response_json['results']:
                    review_exists = Reviews.objects.filter(imdb_id=review['id']).first()
                    if review_exists is None:
                        # create new review in database
                        new_review = {
                            'imdb_id': review['id'],
                            'name': review['author'],
                            'username': review['author_details']['username'],
                            'avatar_path': review['author_details']['avatar_path'],
                            'rating': review['author_details']['rating'],
                            'content': review['content'][:255],
                            'created_at': review['created_at'],
                            'updated_at': review['updated_at'],
                            'imdb_review_url': review['url'],
                        }
                        Reviews.objects.create(**new_review)
                
                # go to next page
                page += 1
                url = f"https://api.themoviedb.org/3/tv/{tvshow.tmdb_id}/reviews?page={page}"
                response = requests.get(url, headers=headers)
                tvshow_response_json = response.json()
        
        tvshow_count += 1

    return {"success": True}

### initial data loading ###
@router.get("/seeding/data")
def reviews_data_loading(request):
    # set headers
    headers = {
        "accept": "application/json",
        "Authorization": config('TMDB_API_TOKEN'),
    }

    page = 1
    max_pages = 500
    total_pages = 0

    print("===== Starting movie reviews data loading =====")
    movie_count = 1

    # get all movies
    movies = Movies.objects.all()
    for movie in movies:
        print(f"===== Movie #{movie_count}: {movie.title}")
        review_list = []

        # get the reviews for a movie
        url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}/reviews?page={page}"
        response = requests.get(url, headers=headers)
        movies_response_json = response.json()

        total_pages = movies_response_json['total_pages']
        if total_pages >= 1:
            # get all the pages we can get
            while page <= max_pages and page <= total_pages:

                # foreach movie get the reviews
                for review in movies_response_json['results']:
                    existing_review = Reviews.objects.filter(imdb_id=review['id']).first()
                    if existing_review is not None:
                        # check if we already have a many to many relationship with this review for the movie
                        review_exists = movie.reviews.filter(id=existing_review.id).exists()
                        if review_exists:
                            continue # skip
                        else:
                            # add review to list to create new many to many relationship
                            review_list.append(existing_review)
                    else:
                        # create a new review
                        new_review = {
                            'imdb_id': review['id'],
                            'name': review['author'],
                            'username': review['author_details']['username'],
                            'avatar_path': review['author_details']['avatar_path'],
                            'rating': review['author_details']['rating'],
                            'content': review['content'][:255],
                            'created_at': review['created_at'],
                            'updated_at': review['updated_at'],
                            'imdb_review_url': review['url'],
                        }
                        review_obj = Reviews.objects.create(**new_review)
                        review_list.append(review_obj)

                if len(review_list) > 0:
                    movie.reviews.set(review_list)
                    movie.save()

                # go to next page
                page += 1
                url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}/reviews?page={page}"
                response = requests.get(url, headers=headers)
                movies_response_json = response.json()

        movie_count += 1

    print("===== Starting tv shows reviews data loading =====")
    tvshow_count = 1

    # get all tv shows
    tvshows = TVShows.objects.all()
    for tvshow in tvshows:
        print(f"===== TV Show #{tvshow_count}: {tvshow.title}")
        review_list = []

        # get the reviews for a tv show
        url = f"https://api.themoviedb.org/3/tv/{tvshow.tmdb_id}/reviews"
        response = requests.get(url, headers=headers)
        tvshow_response_json = response.json()

        total_pages = tvshow_response_json['total_pages']
        if total_pages >= 1:
            # get all the pages we can get
            while page <= max_pages and page <= total_pages:

                # foreach movie get the reviews
                for review in tvshow_response_json['results']:
                    existing_review = Reviews.objects.filter(video_id=review['id']).first()
                    if existing_review is not None:
                        # check if we already have a many to many relationship with this review for the tv show
                        review_exists = movie.reviews.filter(id=existing_review.id).exists()
                        if review_exists:
                            continue # skip
                        else:
                            # add review to list to create new many to many relationship
                            review_list.append(existing_review)
                    else:
                        # create a new tv show
                        new_review = {
                            'imdb_id': review['id'],
                            'name': review['author'],
                            'username': review['author_details']['username'],
                            'avatar_path': review['author_details']['avatar_path'],
                            'rating': review['author_details']['rating'],
                            'content': review['content'][:255],
                            'created_at': review['created_at'],
                            'updated_at': review['updated_at'],
                            'imdb_review_url': review['url'],
                        }
                        review_obj = Reviews.objects.create(**new_review)
                        review_list.append(review_obj)

                if len(review_list) > 0:
                    tvshow.reviews.set(review_list)
                    tvshow.save()

                # go to next page
                page += 1
                url = f"https://api.themoviedb.org/3/tv/{tvshow.tmdb_id}/reviews?page={page}"
                response = requests.get(url, headers=headers)
                tvshow_response_json = response.json()

        tvshow_count += 1

    return {"success": True}

# create new review
@router.post("/", auth=None)
def create_review(request, payload: Review):
    review = Reviews.objects.create(**payload.dict())
    return {"id": review.id}

# get review by id
@router.get("/id/{id}", response=ReviewOut)
def get_review_by_id(request, id: str):
    review = get_object_or_404(Reviews, id=id)
    return review

# get review by imdb_id
@router.get("/imdb_id/{imdb_id}", response=ReviewOut)
def get_review_by_imdb_id(request, imdb_id: str):
    review = get_object_or_404(Reviews, imdb_id=imdb_id)
    return review

# list all reviews
@router.get("/", response=List[ReviewOut])
def list_all_reviews(request):
    review_list = Reviews.objects.all()
    return review_list

# update review by id
@router.put("/id/{id}")
def update_review_by_id(request, id: str, payload: ReviewOut):
    review = get_object_or_404(Reviews, id=id)
    for attr, value in payload.dict().items():
        setattr(review, attr, value)
    review.save()
    return {"success": True}

# update review by imdb_id
@router.put("/imdb_id/{imdb_id}")
def update_review_by_imdb_id(request, imdb_id: str, payload: ReviewOut):
    review = get_object_or_404(Reviews, imdb_id=imdb_id)
    for attr, value in payload.dict().items():
        setattr(review, attr, value)
    review.save()
    return {"success": True}

# delete/disable review by id
@router.delete("/id/{id}")
def delete_review_by_id(request, id: str):
    review = get_object_or_404(Reviews, id=id)
    #review.delete()
    review.enabled = False
    review.archived = True
    review.save()
    return {"success": True}

# delete/disable review by imdb_id
@router.delete("/imdb_id/{imdb_id}")
def delete_review_by_imdb_id(request, imdb_id: str):
    review = get_object_or_404(Reviews, imdb_id=imdb_id)
    #review.delete()
    review.enabled = False
    review.archived = True
    review.save()
    return {"success": True}