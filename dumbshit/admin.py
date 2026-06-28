from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.models import LogEntry

admin.site.unregister(User)

@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ('username', 'is_superuser', 'email', 'id')
    search_fields = ['id', 'username', 'email']

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type')
    search_fields = ['pk', 'user__username']

    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False