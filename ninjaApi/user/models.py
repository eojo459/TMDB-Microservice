import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.fields import ArrayField
from django.db.models.fields.related import ManyToManyField


# https://www.youtube.com/watch?v=Ae7nc1EGv-A
# https://www.youtube.com/watch?v=Z6QMPAcS6E8

# -------------------------------------------------- BASE USERS (ADMIN) -------------------------------------------------- #

class Role(models.TextChoices):
    ADMIN = "ADMIN",
    OWNER = "USER",
    STAFF = "STAFF",

class User(models.Model): 
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    uid = models.UUIDField(default=uuid.uuid4, null=False, unique=True) # supabase id
    username = models.CharField(max_length=50, null=True, blank=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.CharField(max_length=50, null=True, blank=True)
    street = models.CharField(max_length=50, null=True, blank=True)
    street_2 = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    province = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=25, null=True, blank=True)
    country_code = models.CharField(max_length=25, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    role = models.CharField(max_length=20, null=True, blank=True)
    cell_number = models.CharField(max_length=15, null=True, blank=True)
    work_number = models.CharField(max_length=15, null=True, blank=True)
    home_number = models.CharField(max_length=15, null=True, blank=True)
    pin_code = models.CharField(max_length=150, null=True, blank=True)
    password = models.CharField(max_length=150, null=True, blank=True)
    notes = models.CharField(max_length=255, null=True, blank=True)
    last_logged_in = models.DateTimeField(auto_now=True, null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
    confirm_email = models.BooleanField(default=False)
    pending_approval = models.BooleanField(default=True)
    date_of_birth = models.DateField(null=True, blank=True)