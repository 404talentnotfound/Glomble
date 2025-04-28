from django.contrib import admin
from .models import Profile, Chat, Message, ProfileCustomisation


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'shadowbanned', 'username__is_superuser', 'username__email']
    search_fields = ['id', 'username__username', 'username__email']

@admin.register(ProfileCustomisation)
class ProfileCustomisationAdmin(admin.ModelAdmin):
    list_display = ['customised_profile', 'customised_profile__username']
    search_fields = ['customised_profile__id', 'customised_profile__username__username']