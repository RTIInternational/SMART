from django.contrib.auth.models import User as AuthUser
from django.core.management.base import BaseCommand

from core.models import Profile


class Command(BaseCommand):
    help = "Seeds the database with a test profile"

    def add_arguments(self, parser):
        parser.add_argument(
            "--runtasks",
            action="store_true",
            default=False,
            help="Creates a new non-superuser in the database",
        )

    def handle(self, *args, **options):
        try:
            Profile.objects.get(user__username="test")
            print("SEED: Profile Already Exists")
        except Profile.DoesNotExist:
            auth_user = AuthUser.objects.create_user(
                username="test", password="password", email="dummy@smart.org"
            )
            Profile.objects.create(user=auth_user)
            print("SEED: New Profile Created")
