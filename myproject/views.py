from django.shortcuts import redirect
from django.http import JsonResponse
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.google.provider import GoogleProvider
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

# Custom Redirect View for Google login
def google_login_redirect(request):
    app = SocialApp.objects.get(provider=GoogleProvider.id)
    client_id = app.client_id
    redirect_uri = "http://localhost:8000/api/auth/google/callback/"
    scope = " ".join(["email", "profile"])
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}"
        f"&redirect_uri={redirect_uri}&scope={scope}&response_type=code"
    )
    return redirect(auth_url)

# Callback View for Google login
def google_login_callback(request):
    authorization_code = request.GET.get('code')
    
    if not authorization_code:
        return JsonResponse({"error": "Authorization code not found"}, status=400)
    
    app = SocialApp.objects.get(provider=GoogleProvider.id)
    client_id = app.client_id
    client_secret = app.secret
    redirect_uri = "http://localhost:8000/api/auth/google/callback/"
    
    # Google token endpoint
    token_url = "https://oauth2.googleapis.com/token"
    
    # Prepare the data to request the access token
    token_data = {
        'code': authorization_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    # Send the POST request to get the access token
    response = requests.post(token_url, data=token_data)
    
    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch access token", "details": response.json()}, status=500)
    
    token_info = response.json()
    access_token = token_info.get('access_token')
    refresh_token = token_info.get('refresh_token')
    
    if not access_token:
        return JsonResponse({"error": "Access token not found in response"}, status=500)
    
    # Get user info from Google using the access token
    user_data = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    
    # Check if the user exists in the system
    user = User.objects.filter(email=user_data['email']).first()
    
    if not user:
        # If user doesn't exist, create a new user
        user = User.objects.create_user(
            username=user_data['email'], 
            email=user_data['email'], 
            password=None  # Set a default password if needed
            
        )
    
    # Generate JWT token
    refresh = RefreshToken.for_user(user)
    return JsonResponse({
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
    })
