from .models import Video, batch_calculate_score
from profiles.models import Profile
from notifications.models import BaseNotification 
from django.utils import timezone
from Glomble.pc_prod import WEEK_TOMSTAMP, MONTH_TOMSTAMP
from django.contrib.auth.models import User

def recalculate_score():
    batch_calculate_score(Video.objects.all())

def reset_recommendations():
    Video.recommendations.through.objects.all().delete()
    recalculate_score()

# make this
def remove_inactive_users():
    inactive_threshold = WEEK_TOMSTAMP*2 # two (2) weeks (seven (7) days (twenty-four (24) hours (sixty (60) minutes (sixty (60) seconds))))
    for user in User.objects.all().filter(is_active=False):
        if timezone.now().timestamp() - user.date_joined.timestamp() > inactive_threshold:
            user.delete()

def remove_old_notifs():
    inactive_threshold = MONTH_TOMSTAMP*6 # six (6) months (around four and a half (4.5) weeks (seven (7) days (twenty-four (24) hours (sixty (60) minutes (sixty (60) seconds)))))
    for notification in BaseNotification.objects.all():
        if timezone.now().timestamp() -notification.date_notified.timestamp() > inactive_threshold:
            notification.delete()

def remove_bad_things():
    remove_inactive_users()
    remove_old_notifs()
    #remove_everything_else()