import uuid
from django.db import models

class Genres(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    type = models.IntegerField(default=0) # 0=movie | 1=tv
    enabled = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
