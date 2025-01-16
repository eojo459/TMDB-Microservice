from django.apps import AppConfig


class BackendapiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backendApi'

    ## TODO: UNCOMMENT WHEN YOU NEED TO USE SCHEDULER
    def ready(self):
        from backendApi.utils.scheduler import scheduler
        scheduler.start_scheduler()
