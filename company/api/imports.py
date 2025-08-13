# Django Imports
from django.db import DatabaseError
from django.core.exceptions import ObjectDoesNotExist
from django.middleware.csrf import CsrfViewMiddleware  
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import gettext_lazy as _ 
# DRF Imports
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

# drf_yasg Imports (For API documentation)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Custom Imports
from .utils import success_response, error_response, validation_error_response


