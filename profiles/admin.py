from django.contrib import admin
from .models import Profile, Chat, Message, ProfileActivity


admin.site.register(Profile)
admin.site.register(Chat)
admin.site.register(Message)
admin.site.register(ProfileActivity)