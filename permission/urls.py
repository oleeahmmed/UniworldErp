from django.urls import path
from .views import user_permissions_view,group_permissions_view
from django.contrib.auth.views import LogoutView

from .views import (
    UserListView, 
    UserCreateView, 
    UserUpdateView, 
    UserDeleteView, 
    GroupListView, 
    GroupCreateView, 
    GroupUpdateView, 
    GroupDeleteView, 
    PermissionListView, 
    PermissionCreateView, 
    PermissionUpdateView, 
    PermissionDeleteView,
    login_view,
    register_view,
    dashboard_view,
    logout_view
)
app_name = 'permission'  


urlpatterns = [
    path('user/<int:user_id>/roles-and-permissions/', user_permissions_view, name='user_roles_permissions'),
    path('group/<int:group_id>/permissions/', group_permissions_view, name='group_permissions'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/update/', UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),


        # Group URLs
    path('groups/', GroupListView.as_view(), name='group_list'),
    path('groups/create/', GroupCreateView.as_view(), name='group_create'),
    path('groups/<int:pk>/update/', GroupUpdateView.as_view(), name='group_edit'),
    path('groups/<int:pk>/delete/', GroupDeleteView.as_view(), name='group_delete'),


    path('permissions/', PermissionListView.as_view(), name='permission_list'),
    path('permissions/create/', PermissionCreateView.as_view(), name='permission_create'),
    path('permissions/<int:pk>/update/', PermissionUpdateView.as_view(), name='permission_edit'),
    path('permissions/<int:pk>/delete/', PermissionDeleteView.as_view(), name='permission_delete'),
    
    path('',login_view, name='login'),
    path('register/', register_view, name='register'),    
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),

]


