from __future__ import absolute_import
from celery import shared_task

from .models import Project, Data, Label

@shared_task
def test():
    return {'result': 'Test Task complete'}
