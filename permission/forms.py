from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate


# User Form without specifying widgets in Meta
class UserForm(forms.ModelForm):
    # Adding password fields manually
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50',
            'placeholder': 'Enter password'
        }),
        required=False,  # Optional if updating a user (new users will handle password explicitly)
        label='Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50',
            'placeholder': 'Confirm password'
        }),
        required=False,  # Optional for updates
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamically apply CSS classes to all fields
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50'
            })
        
        # Custom style for 'is_active' checkbox field
        self.fields['is_active'].widget.attrs.update({
            'class': 'mt-1'
        })

    # Custom validation for 'password' and 'confirm_password'
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # Ensure passwords match
        if password and confirm_password and password != confirm_password:
            raise ValidationError({'confirm_password': "Passwords do not match."})

        return cleaned_data

    # Custom validation for 'username' field
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        # Only check uniqueness if it's a new user or the username is being changed
        if not self.instance.pk:  # New user (no primary key)
            if User.objects.filter(username=username).exists():
                raise ValidationError("Username already exists. Please choose a different one.")
        
        return username

    # Custom validation for 'email' field
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Only check uniqueness if it's a new user or the email is being changed
        if not self.instance.pk:  # New user (no primary key)
            if User.objects.filter(email=email).exists():
                raise ValidationError("Email is already in use. Please use a different one.")
        
        return email

    # Optional: Custom validation for 'is_active' (if needed)
    def clean_is_active(self):
        is_active = self.cleaned_data.get('is_active')
        # For example, you could disallow deactivating an account if certain conditions apply
        if not is_active:
            # Example condition (can be customized based on your logic)
            raise ValidationError("The user cannot be deactivated.")
        return is_active


# Group Form without specifying widgets in Meta
class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically apply CSS classes to all fields
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50'
            })



from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permission
        fields = ['name', 'codename', 'content_type']  # Fields you want to allow users to edit or create

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically apply CSS classes to all fields
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50'
            })



class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-field', 'placeholder': ' ', 'autocomplete': 'off'}),
        label='Username'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-field', 'placeholder': ' ', 'autocomplete': 'off'}),
        label='Password'
    )

    def clean(self):
        # This method is called during validation to clean all the form fields.
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        # Custom validation: Check if the username exists in the database
        if username and not User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username not found. Please check and try again.")

        # Custom validation: Check if password is empty
        if password and len(password) < 6:
            raise forms.ValidationError("Password should be at least 6 characters long.")

        # Return the cleaned data
        return cleaned_data


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically apply CSS classes to all fields
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50'
            })
    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password != password2:
            raise forms.ValidationError("Passwords do not match")
        return password2