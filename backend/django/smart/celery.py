from __future__ import absolute_import, unicode_literals

import os

import configurations
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")

configurations.setup()

app = Celery("smart")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
