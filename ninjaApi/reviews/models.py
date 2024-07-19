import uuid
from django.db import models

class Reviews(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    imdb_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50)
    username = models.CharField(max_length=50)
    avatar_path = models.CharField(max_length=255)
    rating = models.IntegerField(default=0)
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    review_id = models.CharField(max_length=50)
    updated_at = models.DateTimeField()
    imdb_review_url = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)