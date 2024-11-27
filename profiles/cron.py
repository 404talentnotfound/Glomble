from .models import Profile

def reset_recommendations_left():
    for i in Profile.objects.all():
        i.recommendations_left = 3
        i.save()