# Generated by Django 5.0.7 on 2024-07-19 06:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0002_alter_movies_description_alter_movies_imdb_link_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='movies',
            name='status',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
