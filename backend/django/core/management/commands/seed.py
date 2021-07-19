import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Data, Label, Profile, Project
from core.utils.util import md5_hash

AuthUser = get_user_model()

SEED_USERNAME = "test"
SEED_USERNAME2 = "test2"
SEED_PASSWORD = "password"
SEED_PASSWORD2 = "password2"
SEED_EMAIL = "dummy@smart.org"
SEED_PROJECT = "seed-data"
SEED_FILE_PATH = "./core/data/reddit_sample_awww/test-awww.csv"
SEED_LABELS = ["about cats", "not about cats", "unclear"]


def seed_database(noprofile=False, nodata=False):
    if not noprofile:
        try:
            profile = Profile.objects.get(user__username=SEED_USERNAME)
            print("SEED: test User Already Exists - user.pk: {}".format(profile.pk))
        except Profile.DoesNotExist:
            auth_user = AuthUser.objects.create_user(
                username=SEED_USERNAME, password=SEED_PASSWORD, email=SEED_EMAIL
            )
            profile = Profile.objects.get(user=auth_user)
            print("SEED: New test User Created - profile.pk: {}".format(profile.pk))

            auth_user2 = AuthUser.objects.create_user(
                username=SEED_USERNAME2, password=SEED_PASSWORD2, email=SEED_EMAIL
            )
            profile2 = Profile.objects.get(user=auth_user2)
            print("SEED: New test User Created - profile.pk: {}".format(profile2.pk))

    if not nodata:
        project, created = Project.objects.get_or_create(
            name=SEED_PROJECT, creator=profile
        )
        if not created:
            print(
                "SEED: seed-data Project Already Exists - project.pk: {}".format(
                    project.pk
                )
            )
        else:
            with open(SEED_FILE_PATH) as inf:
                reader = csv.DictReader(inf)
                sample_data = [
                    Data(
                        text=row["Text"],
                        hash=md5_hash(row["Text"]),
                        project=project,
                        upload_id_hash=md5_hash(i),
                    )
                    for i, row in enumerate(reader)
                ]
                Data.objects.bulk_create(sample_data)
            for label in SEED_LABELS:
                Label.objects.create(name=label, project=project)
            print(
                "SEED: seed-data Project Seeded with Data - project.pk: {}".format(
                    project.pk
                )
            )


class Command(BaseCommand):
    help = "Seeds the database with a test profile and sample data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--noprofile",
            action="store_true",
            help="Will not create a new test profile",
        )
        parser.add_argument(
            "--nodata",
            action="store_true",
            help="Will not seed database with sample data",
        )

    def handle(self, *args, **options):
        seed_database(noprofile=options["noprofile"], nodata=options["nodata"])
