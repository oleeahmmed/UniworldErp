from rest_framework import serializers
from ..models import Company, Branch, ContactPerson, CompanyPolicy

from django.contrib.auth.models import User
from ..models import CompanyProfile

# Serializer for Company
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__' 

# Serializer for Branch
class BranchSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)  # Nest the CompanySerializer to show company details

    class Meta:
        model = Branch
        fields = ('id', 'company', 'name', 'address', 'phone', 'email', 'is_active')

# Serializer for ContactPerson
class ContactPersonSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)  # Nest the CompanySerializer to show company details

    class Meta:
        model = ContactPerson
        fields = ('id', 'company', 'name', 'position', 'email', 'phone', 'is_primary_contact')

# Serializer for CompanyPolicy
class CompanyPolicySerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)  # Nest the CompanySerializer to show company details

    class Meta:
        model = CompanyPolicy
        fields = ('id', 'company', 'title', 'description', 'document')



class UserProfileSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='companyprofile.company.name', read_only=True)  # Fetch company name
    company_id = serializers.PrimaryKeyRelatedField(queryset=CompanyProfile.objects.all(), source='companyprofile.company', write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'company_name', 'company_id']

    def update(self, instance, validated_data):
        company_data = validated_data.pop('companyprofile', {})
        company = company_data.get('company', None)
        if company:
            instance.companyprofile.company = company
            instance.companyprofile.save()
        
        return super().update(instance, validated_data)        