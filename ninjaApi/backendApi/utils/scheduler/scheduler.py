import os
from apscheduler.schedulers.background import BackgroundScheduler
from django.shortcuts import get_object_or_404
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.utils import timezone
from django_apscheduler.models import DjangoJobExecution
import sys
from datetime import date, datetime, time, timedelta
from requests import Response
from movies.api import fetch_movies_new_releases_TMDB, fetch_movies_trending_daily_TMDB, fetch_movies_trending_services, fetch_movies_trending_weekly_TMDB
from tvshows.api import fetch_tv_shows_new_releases_TMDB, fetch_tv_shows_trending_daily_TMDB, fetch_tv_shows_trending_services, fetch_tv_shows_trending_weekly_TMDB
from user.models import User
from django.db.models import Q, F
from django_apscheduler import util
from apscheduler.triggers.cron import CronTrigger
from decouple import config
import boto3

session = boto3.session.Session()
client = session.client('s3',
                        region_name=config('VH_SPACES_REGION'),
                        endpoint_url=config('VH_SPACES_ENDPOINT'),
                        aws_access_key_id=config('VH_SPACES_KEY'),
                        aws_secret_access_key=config('VH_SPACES_SECRET'))

@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
  """
  This job deletes APScheduler job execution entries older than `max_age` from the database.
  It helps to prevent the database from filling up with old historical records that are no
  longer useful.
  
  :param max_age: The maximum length of time to retain historical job execution records.
                  Defaults to 7 days.
  """
  DjangoJobExecution.objects.delete_old_job_executions(max_age)

# check and cancel any expired subscriptions
def check_expired_subscriptions():
    # TODO: get the acounts that have ran out of days and remove their subscription access
    pass

# check and deactivate any expired auth accounts
def check_expired_auth_accounts():
    # TODO: get the accounts where end date <= current date
    pass

# get newly released tv shows from TMDB
def update_newly_released_tv_shows():
    print("Running scheduled task - update newly released tv shows")
    fetch_tv_shows_new_releases_TMDB()
    print("Ended scheduled task - update newly released tv shows")
    return

# get trending daily tv shows from TMDB
def update_trending_daily_tv_shows():
    print("Running scheduled task - update trending daily tv shows")
    fetch_tv_shows_trending_daily_TMDB()
    print("Ended scheduled task - update trending daily tv shows")
    return

# get trending weekly tv shows from TMDB
def update_trending_weekly_tv_shows():
    print("Running scheduled task - update trending weekly tv shows")
    fetch_tv_shows_trending_weekly_TMDB()
    print("Ended scheduled task - update trending weekly tv shows")
    return

# get newly released movies from TMDB
def update_newly_released_movies():
    print("Running scheduled task - update newly released movies")
    fetch_movies_new_releases_TMDB()
    print("Ended scheduled task - update newly released movies")
    return

# get trending daily movies from TMDB
def update_trending_daily_movies():
    print("Running scheduled task - update trending daily movies")
    fetch_movies_trending_daily_TMDB()
    print("Ended scheduled task - update trending daily movies")
    return

# get trending weekly movies from TMDB
def update_trending_weekly_movies():
    print("Running scheduled task - update trending weekly movies")
    fetch_movies_trending_weekly_TMDB()
    print("Ended scheduled task - update trending weekly movies")
    return

# get trending tv shows from streaming services
def update_trending_services_tv_shows():
    print("Running scheduled task - update trending services tv shows")
    fetch_tv_shows_trending_services()
    print("Ended scheduled task - update trending services tv shows")
    return

# get trending movies from streaming services
def update_trending_services_movies():
    print("Running scheduled task - update trending services movies")
    fetch_movies_trending_services(150)
    print("Ended scheduled task - update trending services movies")
    return

# start the scheduler
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # update newly released tv shows
    scheduler.add_job(
        update_newly_released_tv_shows, 
        'interval', 
        hours=8,
        id='update_newly_released_tv_shows', 
        max_instances=1,
        replace_existing=True,
    )

    # update trending daily tv shows
    scheduler.add_job(
        update_trending_daily_tv_shows, 
        'interval', 
        hours=8, 
        id='update_trending_daily_tv_shows', 
        max_instances=1,
        replace_existing=True,
    )

    # update trending weekly tv shows
    scheduler.add_job(
        update_trending_weekly_tv_shows, 
        'interval', 
        hours=8, 
        id='update_trending_weekly_tv_shows', 
        max_instances=1,
        replace_existing=True,
    )

    # update newly released movies
    scheduler.add_job(
        update_newly_released_movies, 
        'interval', 
        hours=8, 
        id='update_newly_released_movies', 
        max_instances=1,
        replace_existing=True,
    )

    # update trending daily movies
    scheduler.add_job(
        update_trending_daily_movies, 
        'interval', 
        hours=8, 
        id='update_trending_daily_movies', 
        max_instances=1,
        replace_existing=True,
    )

    # update trending weekly movies
    scheduler.add_job(
        update_trending_weekly_movies, 
        'interval', 
        hours=8, 
        id='update_trending_weekly_movies', 
        max_instances=1,
        replace_existing=True,
    )

    # update trending services tv shows
    scheduler.add_job(
        update_trending_services_tv_shows,
        trigger=CronTrigger(
            day_of_week="mon", hour="00", minute="01"
        ),  # Midnight on Monday
        id="update_trending_services_tv_shows",
        max_instances=1,
        replace_existing=True,
    )

    # update trending services movies
    scheduler.add_job(
        update_trending_services_movies,
        trigger=CronTrigger(
            day_of_week="mon", hour="00", minute="05"
        ),  # Midnight on Monday
        id="update_trending_services_movies",
        max_instances=1,
        replace_existing=True,
    )
 
    # clear and delete old job executions
    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(
            day_of_week="mon", hour="00", minute="00"
        ),  # Midnight on Monday, before start of the next work week.
        id="delete_old_job_executions",
        max_instances=1,
        replace_existing=True,
    )
    register_events(scheduler)
    scheduler.start()
    print("Scheduler started...", file=sys.stdout)