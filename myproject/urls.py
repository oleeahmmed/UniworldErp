from django.contrib import admin
from django.urls import path, re_path, include
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# # from .views import google_login_redirect, google_login_callback


# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
# from rest_framework import permissions

# schema_view = get_schema_view(
#    openapi.Info(
#       title="Your API Title",
#       default_version='v1',
#       description="API description",
#       terms_of_service="https://www.yourcompany.com/terms/",
#       contact=openapi.Contact(email="contact@yourcompany.local"),
#       license=openapi.License(name="BSD License"),
#    ),
#    public=True,
#    permission_classes=(permissions.AllowAny,),
# )

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
   #  path('ckeditor5/', include('django_ckeditor_5.urls')),  # Include CKEditor 5 URLs
   # path('', include('admin_soft.urls')),
   #  path('accounts/', include('allauth.urls')),
   path('', include('permission.urls')),

   #  path('api/auth/', include('dj_rest_auth.urls')),  # dj-rest-auth URLs
   #  path('api/auth/registration/', include('dj_rest_auth.registration.urls')),  # Registration URLs
   #  path('api/auth/google/', google_login_redirect, name='google_login_redirect'),  # Google login redirect URL
   #  path('api/auth/google/callback/', google_login_callback, name='google_login_callback'),  # Callback for Google login
   #  path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # JWT Token Obtain endpoint
   #  path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # JWT Token Refresh endpoint
   #  re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   #  re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   #  re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('company/', include('company.urls')),
   #  path('company-management/', include('company.api.urls')),  
    path('erp/', include('uniworlderp.urls')),


]
# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)