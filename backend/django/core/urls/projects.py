from django.conf.urls import url, include
from core.views import frontend

urlpatterns = [
    url(r'^projects/$', frontend.ProjectList.as_view(), name='project_list'),
    url(r'^projects/add/$', frontend.ProjectCreate.as_view(), name='project_create'),
    url(r'^projects/(?P<pk>\d+)/$', frontend.ProjectDetail.as_view(), name='project_detail'),
    url(r'^projects/(?P<pk>\d+)/update/$', frontend.ProjectUpdate.as_view(), name='project_update'),
    url(r'^projects/(?P<pk>\d+)/delete/$', frontend.ProjectDelete.as_view(), name='project_delete'),
    url(r'^projects/(?P<pk>\d+)/code/$', frontend.ProjectCode.as_view(), name='project_code'),
]