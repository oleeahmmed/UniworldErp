
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from django.contrib import admin
from .models import Company, Branch, ContactPerson, CompanyPolicy,CompanyProfile

admin.site.register(Company)
admin.site.register(Branch)
admin.site.register(ContactPerson)
admin.site.register(CompanyPolicy)



# Inline class to display the CompanyProfile in the User admin
class CompanyProfileInline(admin.StackedInline):
    model = CompanyProfile
    can_delete = False
    verbose_name_plural = ''  # Set this to empty string to remove the label
    def save_model(self, request, obj, form, change):
        # Ensure only one picture source is used
        if obj.profile_picture and obj.picture_url:
            obj.picture_url = None  # Prioritize uploaded images
        super().save_model(request, obj, form, change)
# Create a custom UserAdmin that includes the CompanyProfileInline and default user fields
class UserAdmin(DefaultUserAdmin):
    # Add the CompanyProfileInline as an inline model to show company details in the user form
    inlines = [CompanyProfileInline]

    # Do not include 'company' directly in fieldsets, as it is not part of User model
    # Just keep the default fieldsets and let the inline manage the company data
    fieldsets = DefaultUserAdmin.fieldsets

    # Add a custom method to retrieve the company for the user
    def get_company(self, obj):
        # Access the company through the related CompanyProfile model
        return obj.companyprofile.company.name if obj.companyprofile else None
    get_company.admin_order_field = 'company'  # Allows sorting by company
    get_company.short_description = 'Company'  # Column header in the admin list

    # Update list_display to include the custom get_company method
    list_display = DefaultUserAdmin.list_display + ('get_company',)

# Unregister the default User admin
admin.site.unregister(User)

# Re-register the User model with the custom UserAdmin
admin.site.register(User, UserAdmin)