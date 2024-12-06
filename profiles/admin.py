from django.contrib import admin
from .models import Profile, Chat, Message, ProfileCustomisation


admin.site.register(Profile)
admin.site.register(Chat)
admin.site.register(Message)
admin.site.register(ProfileCustomisation)
