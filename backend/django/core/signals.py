from allauth.account.signals import user_logged_out
from django.db.models import Q
from django.dispatch import receiver

from core.models import Profile, Project
from core.utils.utils_annotate import leave_coding_page


@receiver(user_logged_out)
def on_user_logout(sender, **kwargs):
    profile = Profile.objects.get(pk=kwargs["user"].pk)
    profile_projects = Project.objects.filter(
        Q(creator=profile) | Q(projectpermissions__profile=profile)
    ).distinct()

    for project in profile_projects:
        leave_coding_page(profile, project)
