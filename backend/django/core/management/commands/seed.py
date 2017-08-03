import os.path
import csv

from django.core.management.base import BaseCommand, CommandError

from django.contrib.auth.models import User as AuthUser
from core.models import User as User, Project, Label, Data

SEED_USERNAME = 'test'
SEED_PASSWORD = 'password'
SEED_EMAIL = 'dummy@smart.org'
SEED_PROJECT = 'seed-data'
SEED_FILE_PATH = './core/data/SemEval-2016-Task6/train-feminism.csv'
SEED_LABELS = ['AGAINST', 'FAVOR', 'NONE']

def seed_database(nouser=False, nodata=False):
    if not nouser:
        try:
            user = User.objects.get(auth_user__username=SEED_USERNAME)
            print("SEED: test User Already Exists - user.pk: {}".format(user.pk))
        except User.DoesNotExist:
            auth_user = AuthUser.objects.create_user(username=SEED_USERNAME, password=SEED_PASSWORD, email=SEED_EMAIL)
            user = User.objects.create(auth_user=auth_user)
            print("SEED: New test User Created - user.pk: {}".format(user.pk))

    if not nodata:
        project, created = Project.objects.get_or_create(name=SEED_PROJECT)
        if not created:
            print('SEED: seed-data Project Already Exists - project.pk: {}'.format(project.pk))
        else:
            with open(SEED_FILE_PATH) as inf:
                reader = csv.DictReader(inf)
                sample_data = [Data(text=row['Tweet'], project=project) for row in reader]
                dataset = Data.objects.bulk_create(sample_data)
            for label in SEED_LABELS:
                Label.objects.create(name=label, project=project)
            print('SEED: seed-data Project Seeded with Data - project.pk: {}'.format(project.pk))


class Command(BaseCommand):
    help = 'Seeds the database with a test user and sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nouser',
            action='store_true',
            help="Will not create a new test user"
        )
        parser.add_argument(
            '--nodata',
            action='store_true',
            help="Will not seed database with sample data"
        )

    def handle(self, *args, **options):
        seed_database(nouser=options['nouser'],
                      nodata=options['nodata'])
