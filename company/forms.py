from django import forms
from .models import Company,Branch,ContactPerson, CompanyPolicy

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name',
            'registration_number',
            'established_date',
            'email',
            'phone',
            'address',
            'website',
            'logo',
            'is_active',
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamically apply widgets to all fields
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50 px-2'
            })
        
        # Customize the 'is_active' checkbox field
        self.fields['is_active'].widget.attrs.update({
            'class': 'mt-1 '
        })
        
        # You can customize specific fields here if needed, e.g., 'logo' field
        self.fields['logo'].widget.attrs.update({
            'class': (
                'mt-1 block w-full text-sm text-[hsl(var(--muted-foreground))] '
                'file:mr-4 file:py-2 file:px-4 '
                'file:rounded-full file:border-0 '
                'file:text-sm file:font-semibold '
                'file:bg-[hsl(var(--secondary))] file:text-[hsl(var(--secondary-foreground))] '
                'hover:file:bg-[hsl(var(--accent))]'
            )
        })

        # Set the 'established_date' field to use a date input type
        self.fields['established_date'].widget = forms.DateInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50 px-2',
            'type': 'date'  # This sets the input type to date
        })

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['company', 'name',  'phone', 'email', 'is_active','address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically apply widgets to all fields
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50'
            })
        
        # Customize the 'is_active' checkbox field
        self.fields['is_active'].widget.attrs.update({
            'class': 'mt-1 '
        })
        
        # Customize the 'company' select field with a specific class
        self.fields['company'].widget.attrs.update({
            'class': 'mt-1  rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50'
        })



class ContactPersonForm(forms.ModelForm):
    class Meta:
        model = ContactPerson
        fields = [
            'company',
            'branch',
            'name',
            'position',
            'email',
            'phone',
            'is_primary_contact',
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50'
            })
        # Customize the 'is_primary_contact' checkbox field
        self.fields['is_primary_contact'].widget.attrs.update({
            'class': 'mt-1 '
        })
class CompanyPolicyForm(forms.ModelForm):
    class Meta:
        model = CompanyPolicy
        fields = ['company', 'title', 'description', 'document']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50'
            })

        # You can customize specific fields here if needed, e.g., 'logo' field
        self.fields['document'].widget.attrs.update({
            'class': (
                'mt-1 block w-full text-sm text-[hsl(var(--muted-foreground))] '
                'file:mr-4 file:py-2 file:px-4 '
                'file:rounded-full file:border-0 '
                'file:text-sm file:font-semibold '
                'file:bg-[hsl(var(--secondary))] file:text-[hsl(var(--secondary-foreground))] '
                'hover:file:bg-[hsl(var(--accent))]'
            )
        })            