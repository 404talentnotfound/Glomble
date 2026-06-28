from django.db.models.signals import class_prepared

def longer_username(sender, *args, **kwargs):
    if sender.__name__ == "User" and sender.__module__ == "django.contrib.auth.models":
        sender._meta.get_field("username").max_length = 20
        
class_prepared.connect(longer_username)
