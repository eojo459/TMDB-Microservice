# Generated by Django 5.0.7 on 2024-09-07 18:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tvshows', '0007_alter_episodes_runtime'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='episodes',
            name='tv_show_id',
        ),
        migrations.AddField(
            model_name='episodes',
            name='tv_show_id',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='tv_show_id', to='tvshows.tvshows'),
            preserve_default=False,
        ),
    ]