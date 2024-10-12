from django.shortcuts import redirect
from django.urls import reverse
from .models import Profile

class CheckProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not Profile.objects.filter(username=request.user.id).exists() and not request.path == reverse('create-profile'):
            return redirect('create-profile')
        response = self.get_response(request)

        return response