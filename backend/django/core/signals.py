from allauth.account.signals import user_logged_out
from django.dispatch import receiver

from core.models import Project
from core.utils.utils_annotate import leave_coding_page


@receiver(user_logged_out)
def on_user_logout(sender, **kwargs):
    profile = kwargs["user"].pk
    qs = Project.objects.filter(creator=profile) | Project.objects.filter(
        projectpermissions__profile=profile
    )
    profile_projects = qs.distinct()
    for project in profile_projects:
        print("Removing user", profile, "from coding page for project", project)
        leave_coding_page(profile, project)
