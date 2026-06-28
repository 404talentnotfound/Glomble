from django.contrib import admin
from .models import Profile, Chat, ProfileCustomisation, ProfileRating, Ban, BanAppeal

@admin.action(description="Mark as shadowbanned")
def make_shadowbanned(modeladmin, request, queryset):
    queryset.update(shadowbanned=True)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['username', 'shadowbanned', 'banned', 'username__is_superuser', 'moderator', 'username__email', 'rating', 'id']
    search_fields = ['id', 'username__username', 'username__email']
    actions = [make_shadowbanned]

@admin.register(ProfileRating)
class ProfileRatingAdmin(admin.ModelAdmin):
    list_display = ['id', 'rater', 'rated_profile__username', 'rating']
    search_fields = ['id', 'rated_profile__id', 'rating']

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = ['id']

@admin.register(ProfileCustomisation)
class ProfileCustomisationAdmin(admin.ModelAdmin):
    list_display = ['customised_profile', 'customised_profile__username']
    search_fields = ['customised_profile__id', 'customised_profile__username__username']

@admin.register(Ban)
class BanAdmin(admin.ModelAdmin):
    list_display = ['profile__username', 'description', 'id']
    search_fields = ['profile__username__username', 'description']

@admin.register(BanAppeal)
class BanAppealAdmin(admin.ModelAdmin):
    list_display = ['pk', 'ban__profile__username']
    search_fields = ['pk', 'ban__profile__username']