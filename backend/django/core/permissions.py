from rest_framework import permissions

from core.models import Data, Project
from core.templatetags import project_extras


class IsAdminOrCreator(permissions.BasePermission):
    """Checks if the requestor of the endpoint is admin or creator of a project."""

    message = "Invalid permission. Must be an admin"

    def has_permission(self, request, view):
        if "project_pk" in view.kwargs:
            project = Project.objects.get(pk=view.kwargs["project_pk"])
        elif "data_pk" in view.kwargs:
            project = Data.objects.get(pk=view.kwargs["data_pk"]).project
        else:
            return False

        return project_extras.proj_permission_level(project, request.user.profile) > 1


class IsCoder(permissions.BasePermission):
    """Checks if the requestor of the endpoint is coder (or higher permission) of a
    project.

    Use pk_kwarg_mapping dictionary to map from the request.path to the appropriate type
    of pk
    """

    message = (
        "Account disabled by administrator.  Please contact project owner for details"
    )

    def has_permission(self, request, view):
        if "project_pk" in view.kwargs:
            project = Project.objects.get(pk=view.kwargs["project_pk"])
        elif "data_pk" in view.kwargs:
            project = Data.objects.get(pk=view.kwargs["data_pk"]).project
        else:
            return False

        return project_extras.proj_permission_level(project, request.user.profile) > 0
