from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, BranchViewSet, ContactPersonViewSet, CompanyPolicyViewSet,UserProfileView

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'branches', BranchViewSet)
router.register(r'contactpersons', ContactPersonViewSet)
router.register(r'companypolicies', CompanyPolicyViewSet)

# The router will automatically generate the URL patterns for the viewsets.
urlpatterns = [
    path('api/', include(router.urls)),  
    path('profile/', UserProfileView.as_view(), name='user-profile'),

]
