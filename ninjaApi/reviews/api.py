from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from reviews.models import Reviews

router = Router()

################
# MODEL SCHEMAS
################
class Review(Schema):
    imdb_id: str
    name: str
    username: str
    avatar_path: str
    rating: int
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
    avatar_path: str
    rating: int
    content: str
    created_at: datetime
    updated_at: datetime
    review_id: str
    imdb_review_url: str

################################
# API CONTROLLER METHODS
################################

# create new review
@router.post("/", auth=None)
def create_review(request, payload: Review):
    review = Reviews.objects.create(**payload.dict())
    return {"id": review.id}

# get review by id
@router.get("/reviews/id/{id}", response=ReviewOut)
def get_review_by_id(request, id: str):
    review = get_object_or_404(Reviews, id=id)
    return review

# get review by imdb_id
@router.get("/reviews/imdb_id/{imdb_id}", response=ReviewOut)
def get_review_by_imdb_id(request, imdb_id: str):
    review = get_object_or_404(Reviews, imdb_id=imdb_id)
    return review

# list all reviews
@router.get("/reviews/", response=List[ReviewOut])
def list_all_reviews(request):
    review_list = Reviews.objects.all()
    return review_list

# update review by id
@router.put("/reviews/id/{id}")
def update_review_by_id(request, id: str, payload: ReviewOut):
    review = get_object_or_404(Reviews, id=id)
    for attr, value in payload.dict().items():
        setattr(review, attr, value)
    review.save()
    return {"success": True}

# update review by imdb_id
@router.put("/reviews/imdb_id/{imdb_id}")
def update_review_by_imdb_id(request, imdb_id: str, payload: ReviewOut):
    review = get_object_or_404(Reviews, imdb_id=imdb_id)
    for attr, value in payload.dict().items():
        setattr(review, attr, value)
    review.save()
    return {"success": True}

# delete/disable review by id
@router.delete("/reviews/id/{id}")
def delete_review_by_id(request, id: str):
    review = get_object_or_404(Reviews, id=id)
    #review.delete()
    review.enabled = False
    review.archived = True
    review.save()
    return {"success": True}

# delete/disable review by imdb_id
@router.delete("/reviews/imdb_id/{imdb_id}")
def delete_review_by_imdb_id(request, imdb_id: str):
    review = get_object_or_404(Reviews, imdb_id=imdb_id)
    #review.delete()
    review.enabled = False
    review.archived = True
    review.save()
    return {"success": True}