# Tasks for Celery
from celery import shared_task

@shared_task
def test():
    return print("Test Task run")