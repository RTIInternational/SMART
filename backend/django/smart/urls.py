"""smart URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from core import views

api_router = routers.DefaultRouter()
api_router.register(r'users', views.UserViewSet)
api_router.register(r'auth_users', views.AuthUserViewSet)
api_router.register(r'auth_groups', views.AuthUserGroupViewSet)
api_router.register(r'projects', views.ProjectViewSet)
api_router.register(r'models', views.ModelViewSet)
api_router.register(r'data', views.DataViewSet)
api_router.register(r'data_labels', views.DataLabelViewSet)
api_router.register(r'data_predictions', views.DataPredictionViewSet)
api_router.register(r'queue', views.QueueViewSet)
api_router.register(r'data_queues', views.QueueViewSet)
api_router.register(r'assigned_data', views.AssignedDataViewSet)

urlpatterns = [
    url(r'^api/', include(api_router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^admin/', admin.site.urls),
]
