from django import template

register = template.Library()


@register.simple_tag
def proj_permission_level(project, profile):
    """Given a project and profile return their permission level.

    Args:
        project: a core.models.Project object
        profile: a core.models.Profile object
    Returns:
        permission_level: (int)
            0: no permissions
            1: coder
            2: admin
            3: creator
    """
    if project.creator == profile:
        return 3
    elif any(
        perm.profile == profile and perm.permission == "ADMIN"
        for perm in project.projectpermissions_set.all()
    ):
        return 2
    elif any(
        perm.profile == profile and perm.permission == "CODER"
        for perm in project.projectpermissions_set.all()
    ):
        return 1
    else:
        return 0


proj_permission_level = register.filter("proj_permission_level", proj_permission_level)
