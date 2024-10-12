from django.contrib import admin
from .models import Creator, CreatorFund, CreatorGroup

# Register your models here.
admin.site.register(Creator)
admin.site.register(CreatorFund)
admin.site.register(CreatorGroup)