from django.conf.urls import re_path

from core.views import frontend

app_name = "core"

urlpatterns = [
    re_path(r"^projects/$", frontend.ProjectList.as_view(), name="project_list"),
    re_path(
        r"^projects/add/$",
        frontend.ProjectCreateWizard.as_view(),
        name="project_create",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/$",
        frontend.ProjectDetail.as_view(),
        name="project_detail",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/update/$",
        frontend.ProjectUpdateLanding.as_view(),
        name="project_update_landing",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/update/overview/$",
        frontend.ProjectUpdateOverview.as_view(),
        name="project_update_overview",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/update/data/$",
        frontend.ProjectUpdateData.as_view(),
        name="project_update_data",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/update/codebook/$",
        frontend.ProjectUpdateCodebook.as_view(),
        name="project_update_codebook",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/update/permissions/$",
        frontend.ProjectUpdatePermissions.as_view(),
        name="project_update_permissions",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/update/label/$",
        frontend.ProjectUpdateLabel.as_view(),
        name="project_update_labels",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/delete/$",
        frontend.ProjectDelete.as_view(),
        name="project_delete",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/code/$",
        frontend.ProjectCode.as_view(),
        name="project_code",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/admin/$",
        frontend.ProjectAdmin.as_view(),
        name="project_admin",
    ),
]
