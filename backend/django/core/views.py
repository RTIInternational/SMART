from django.shortcuts import render
from django.contrib.auth.models import Group, User as AuthUser
from django.conf import settings
from rest_framework import viewsets

from core.serializers import (UserSerializer, AuthUserGroupSerializer,
                              AuthUserSerializer)
from core.models import User

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class AuthUserGroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = AuthUserGroupSerializer

class AuthUserViewSet(viewsets.ModelViewSet):
    queryset = AuthUser.objects.all()
    serializer_class = AuthUserSerializer
