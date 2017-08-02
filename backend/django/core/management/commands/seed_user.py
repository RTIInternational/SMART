import os.path

from django.core.management.base import BaseCommand, CommandError

from django.contrib.auth.models import User

from core.models import User as AppUser

class Command(BaseCommand):
    help = 'Seeds the database with a test user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--runtasks',
            action='store_true',
            default=False,
            help='Creates a new non-superuser in the database'
        )

    def handle(self, *args, **options):
        try:
            app_user = AppUser.objects.get(auth_user__username='test')
            print("SEED: User Already Exists")
        except AppUser.DoesNotExist:
            user = User.objects.create_user(username='test', password='password', email='dummy@smart.org')
            app_user = AppUser.objects.create(auth_user=user)
            print("SEED: New User Created")
