from .models import Profile

def reset_recommendations_left():
    profiles = Profile.objects.all()

    for i in profiles:
        i.recommendations_left = 1

    Profile.objects.bulk_update(profiles, ['recommendations_left'])