import uuid
from django.db import models

class Reviews(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    imdb_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    avatar_path = models.CharField(max_length=255, blank=True, null=True)
    rating = models.IntegerField(default=0, blank=True, null=True)
    content = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()
    review_id = models.CharField(max_length=50)
    updated_at = models.DateTimeField()
    imdb_review_url = models.CharField(max_length=255, blank=True, null=True)
    enabled = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)