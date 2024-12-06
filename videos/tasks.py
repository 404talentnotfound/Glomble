from django.core.cache import cache
from django.utils import timezone
from .models import Video

def update_video_view_count(user_id, video_id):
    key = f"user:{user_id}:video:{video_id}"
    start_time = cache.get(key)
    if start_time is None:
        start_time = timezone.now().timestamp()
        cache.set(key, start_time, timeout=None)

    elapsed_time = timezone.now().timestamp() - start_time
    if elapsed_time >= 0.7 * Video.objects.get(id=video_id).duration:
        if not cache.get(f"{key}:viewed"):
            video = Video.objects.get(id=video_id)
            video.views.add(user_id)
            video.save()
            cache.set(f"{key}:viewed", 1, timeout=None)
            return True

    return False

