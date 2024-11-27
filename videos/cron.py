from .models import Video

def reset_recommendations():
    for i in Video.objects.all():
        i.recommendations = 0
        i.save()