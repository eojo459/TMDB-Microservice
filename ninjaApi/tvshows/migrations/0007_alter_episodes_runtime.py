# Generated by Django 5.0.7 on 2024-09-07 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tvshows', '0006_episodes_tv_show_id_episodes_tv_show_tmdb_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episodes',
            name='runtime',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
