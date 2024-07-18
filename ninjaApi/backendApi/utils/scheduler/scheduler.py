import os
from apscheduler.schedulers.background import BackgroundScheduler
from django.shortcuts import get_object_or_404
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.utils import timezone
from django_apscheduler.models import DjangoJobExecution
import sys
from datetime import date, datetime, time, timedelta
from requests import Response
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

# start the scheduler
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # check for expired subscriptions everyday
    scheduler.add_job(
        check_expired_subscriptions, 
        'cron', 
        day_of_week='mon-sun',
        hour='1',
        # 'interval', 
        # hours=24, 
        id='check_expired_subscriptions', 
        max_instances=1,
        replace_existing=True,
    )

    # check for expired auth accounts everyday
    scheduler.add_job(
        check_expired_auth_accounts, 
        'cron', 
        day_of_week='mon-sun',
        hour='1', 
        # 'interval',
        # minutes=2,
        id='check_expired_auth_accounts', 
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