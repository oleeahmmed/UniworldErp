from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator,FileExtensionValidator
from django.conf import settings  
from django.core.exceptions import ObjectDoesNotExist

# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    registration_number = models.CharField(max_length=100, unique=True)  
    established_date = models.DateField()
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', validators=[FileExtensionValidator(['png', 'jpg', 'jpeg'])], blank=True, null=True)
    logo_url = models.URLField(validators=[URLValidator()], blank=True, null=True)  

    is_active = models.BooleanField(default=True)  
    created_at = models.DateTimeField(auto_now_add=True, null=True) 
    updated_at = models.DateTimeField(auto_now=True, null=True)  


    # Add default value for ForeignKey fields to handle migration
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Allow blank values in admin forms
        related_name='companies_created',
        default=None  # Ensure compatibility with existing data
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies_updated',
        default=None
    )

 
    def __str__(self):
        return self.name
    
    def get_picture(self):
        """Returns the profile picture URL (uploaded or external)."""
        if self.profile_picture:
            return self.profile_picture.url
        elif self.picture_url:
            return self.picture_url
        return None
    
    def get_company_logo(self):
        """Returns the company logo URL (uploaded or external)."""
        try:
            # First check if the logo field is populated with an image
            if self.logo:
                return self.logo.url
            # If no logo image, check if the logo_url is populated
            elif self.logo_url:
                return self.logo_url
            # If neither is available, return a default image
            return '/static/images/default-company-logo.png'  # You can change this path to your default image
        except ObjectDoesNotExist:
            # In case of any database-related issue, return a fallback logo
            return '/static/images/default-company-logo.png'


class Branch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.company.name}"



class ContactPerson(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_contacts", blank=True, null=True)  # Optional link to Company
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="contacts", blank=True, null=True)  # Optional link to Branch
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    is_primary_contact = models.BooleanField(default=False)  

    def __str__(self):
        if self.branch:
            return f"{self.name} - {self.position} ({self.branch.name}, {self.branch.company.name})"
        elif self.company:
            return f"{self.name} - {self.position} (Company: {self.company.name})"
        else:
            return f"{self.name} - {self.position}"
    

class CompanyPolicy(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="policies")
    title = models.CharField(max_length=255)
    description = models.TextField()
    document = models.FileField(upload_to="company_policies/", blank=True, null=True)  

    def __str__(self):
        return f"{self.title} - {self.company.name}"    
    

class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_profiles')

    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    picture_url = models.URLField(validators=[URLValidator()], blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.company.name}"

    def get_picture(self):
        """Returns the profile picture URL (uploaded or external)."""
        if self.profile_picture:
            return self.profile_picture.url
        elif self.picture_url:
            return self.picture_url
        return None