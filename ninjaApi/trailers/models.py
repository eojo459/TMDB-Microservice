import uuid
from django.db import models

class Trailers(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=100)
    site = models.CharField(max_length=50)
    quality = models.IntegerField(default=720)
    type = models.CharField(max_length=20)
    official = models.BooleanField(default=False)
    published_at = models.DateTimeField()
    video_id = models.CharField(max_length=50)
    enabled = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)