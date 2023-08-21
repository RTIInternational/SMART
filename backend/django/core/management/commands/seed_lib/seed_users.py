from django.contrib.auth import get_user_model
from core.models import Profile

# https://docs.djangoproject.com/en/4.2/topics/auth/customizing/#django.contrib.auth.get_user_model
AuthUser = get_user_model()


def seed_users():
    # https://docs.djangoproject.com/en/4.2/topics/auth/default/#creating-users
    root_user = AuthUser.objects.create_user(
        username="root", password="password555", email="test@test.com"
    )
    tom_user = AuthUser.objects.create_user(
        username="tom", password="password555", email="test@test.com"
    )
    jade_user = AuthUser.objects.create_user(
        username="jade", password="password555", email="test@test.com"
    )

    return (
        Profile.objects.get(user=root_user),
        Profile.objects.get(user=tom_user),
        Profile.objects.get(user=jade_user),
    )
