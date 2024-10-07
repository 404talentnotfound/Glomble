from django.contrib import admin
from .models import VideoNotification, BaseNotification, UpdateNotification

# Register your models here.

admin.site.register(VideoNotification)
admin.site.register(BaseNotification)
admin.site.register(UpdateNotification)
