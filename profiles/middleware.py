from django.shortcuts import redirect
from django.urls import reverse
from .models import Profile, Ban
from django.contrib.auth.models import User
from .views import create_profile

class CheckProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):        
        response = self.get_response(request)
        
        if request.user.is_authenticated and User.objects.filter(id=request.user.id).exists():            
            if not Profile.objects.filter(username=request.user).exists():
                create_profile(request.user)
            
            profile = Profile.objects.get(username=request.user)
            if profile.banned and request.path not in [reverse('ban-page'), reverse('ban-appeal')]:
                ban = Ban.objects.filter(profile=profile)
                if not ban.exists():
                    profile.banned=False
                    profile.save()
                return redirect("ban-page")

        return response