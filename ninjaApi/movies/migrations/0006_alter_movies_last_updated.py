# Generated by Django 5.0.7 on 2024-09-07 03:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0005_movies_backdrop_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movies',
            name='last_updated',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
