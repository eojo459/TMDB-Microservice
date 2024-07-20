import uuid
from django.db import models

class Peoples(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)
    original_name = models.CharField(max_length=50, null=True, blank=True)
    avatar_path = models.CharField(max_length=255, null=True, blank=True)
    known_for_department = models.CharField(max_length=50, null=True, blank=True)
    popularity = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
    last_updated = models.DateTimeField(null=True, blank=True)