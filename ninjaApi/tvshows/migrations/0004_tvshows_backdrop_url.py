# Generated by Django 5.0.7 on 2024-08-30 03:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tvshows', '0003_tvshows_reviews'),
    ]

    operations = [
        migrations.AddField(
            model_name='tvshows',
            name='backdrop_url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
