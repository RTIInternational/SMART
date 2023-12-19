"""smart URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  re_path(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  re_path(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import re_path, include
    2. Add a URL to urlpatterns:  re_path(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include, re_path
from django.contrib import admin
from django.http import HttpResponseRedirect
from rest_framework_swagger.views import get_swagger_view

urlpatterns = [
    re_path(r"^$", lambda r: HttpResponseRedirect("projects/")),
    re_path(r"^api/", include("core.urls.api")),
    re_path(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^rest-auth/", include("rest_auth.urls")),
    re_path(r"^rest-auth/registration/", include("rest_auth.registration.urls")),
    re_path(r"^accounts/", include("allauth.urls")),
    re_path(r"^", include("core.urls.projects", namespace="projects")),
]

# Don't show API docs in production
if settings.DEBUG:
    swagger_docs_view = get_swagger_view(title="SMART")

    urlpatterns.append(re_path(r"^docs/", swagger_docs_view))
