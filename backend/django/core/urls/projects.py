from django.conf.urls import url
from core.views import frontend

urlpatterns = [
    url(r'^projects/$', frontend.ProjectList.as_view(), name='project_list'),
    url(r'^projects/add/$', frontend.ProjectCreateWizard.as_view(), name='project_create'),
    url(r'^projects/(?P<pk>\d+)/$', frontend.ProjectDetail.as_view(), name='project_detail'),
    url(r'^projects/(?P<pk>\d+)/update/$', frontend.ProjectUpdateLanding.as_view(), name='project_update_landing'),
    url(r'^projects/(?P<pk>\d+)/update/overview/$', frontend.ProjectUpdateOverview.as_view(), name='project_update_overview'),
    url(r'^projects/(?P<pk>\d+)/update/data/$', frontend.ProjectUpdateData.as_view(), name='project_update_data'),
    url(r'^projects/(?P<pk>\d+)/update/codebook/$', frontend.ProjectUpdateCodebook.as_view(), name='project_update_codebook'),
    url(r'^projects/(?P<pk>\d+)/update/permissions/$', frontend.ProjectUpdatePermissions.as_view(), name='project_update_permissions'),
    url(r'^projects/(?P<pk>\d+)/update/label/$', frontend.ProjectUpdateLabel.as_view(), name='project_update_labels'),
    url(r'^projects/(?P<pk>\d+)/delete/$', frontend.ProjectDelete.as_view(), name='project_delete'),
    url(r'^projects/(?P<pk>\d+)/code/$', frontend.ProjectCode.as_view(), name='project_code'),
    url(r'^projects/(?P<pk>\d+)/admin/$', frontend.ProjectAdmin.as_view(), name='project_admin')
]
