from __future__ import absolute_import
from celery import shared_task
from celery.exceptions import Ignore
import csv

from .models import Project, Data, Label

@shared_task
def test():
    return "Test Task run"