# Generated by Django 5.0.7 on 2024-07-19 01:18

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('uid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('username', models.CharField(blank=True, max_length=50, null=True)),
                ('first_name', models.CharField(blank=True, max_length=50, null=True)),
                ('last_name', models.CharField(blank=True, max_length=50, null=True)),
                ('email', models.CharField(blank=True, max_length=50, null=True)),
                ('street', models.CharField(blank=True, max_length=50, null=True)),
                ('street_2', models.CharField(blank=True, max_length=50, null=True)),
                ('city', models.CharField(blank=True, max_length=50, null=True)),
                ('province', models.CharField(blank=True, max_length=50, null=True)),
                ('country', models.CharField(blank=True, max_length=25, null=True)),
                ('country_code', models.CharField(blank=True, max_length=25, null=True)),
                ('postal_code', models.CharField(blank=True, max_length=10, null=True)),
                ('gender', models.CharField(blank=True, max_length=10, null=True)),
                ('role', models.CharField(blank=True, max_length=20, null=True)),
                ('cell_number', models.CharField(blank=True, max_length=15, null=True)),
                ('work_number', models.CharField(blank=True, max_length=15, null=True)),
                ('home_number', models.CharField(blank=True, max_length=15, null=True)),
                ('pin_code', models.CharField(blank=True, max_length=150, null=True)),
                ('password', models.CharField(blank=True, max_length=150, null=True)),
                ('notes', models.CharField(blank=True, max_length=255, null=True)),
                ('last_logged_in', models.DateTimeField(auto_now=True, null=True)),
                ('password_changed_at', models.DateTimeField(blank=True, null=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('archived', models.BooleanField(default=False)),
                ('confirm_email', models.BooleanField(default=False)),
                ('pending_approval', models.BooleanField(default=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
            ],
        ),
    ]
