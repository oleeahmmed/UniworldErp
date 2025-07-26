from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

# Custom Permission Admin
class PermissionAdmin(admin.ModelAdmin):
    # Display the fields in the admin list view
    list_display = ('name', 'codename', 'content_type')
    search_fields = ['name', 'codename']

    # Allow editing the permission details
    fieldsets = (
        (None, {
            'fields': ('name', 'codename', 'content_type')  # Removed 'group_permissions' here
        }),
    )

    # Make sure that permissions can be filtered and grouped
    list_filter = ('content_type',)

# Register the Permission model with the custom admin interface
admin.site.register(Permission, PermissionAdmin)
