# Generated by Django 5.0.7 on 2024-07-19 06:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trailers', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trailers',
            name='tmdb_id',
        ),
    ]
