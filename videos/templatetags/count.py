from django import template
from reports.models import VideoReport, ProfileReport, BugReport, Suggestion
from profiles.models import Profile, BanAppeal
from videos.models import Comment, Video
from django.db.models import Count
from django.urls import reverse
from django.utils.html import escape
from django.utils import timezone
import datetime
import re
from Glomble.pc_prod import LOCAL, DEVELOPER_IDS, CREATOR_ID

register = template.Library()

@register.simple_tag
def V_reports():
    return VideoReport.objects.all().count() > 0

@register.simple_tag
def P_reports():
    return ProfileReport.objects.all().count() > 0

@register.simple_tag
def B_reports():
    return BugReport.objects.all().count() > 0

@register.simple_tag
def S_reports():
    return Suggestion.objects.all().count() > 0

@register.simple_tag
def any_reports():
    return (V_reports() or P_reports() or B_reports() or S_reports())

@register.simple_tag
def any_appeals():
    return BanAppeal.objects.all().exclude(rejected=True).count()

@register.simple_tag
def has_notifications(user_object):
    if Profile.objects.all().filter(username=user_object).exists():
        return Profile.objects.all().get(username=user_object).basenotification_set.all().filter(read=False).count() > 0
    else:
        return False

@register.simple_tag
def can_recommend(video_id, user_object):
    if Profile.objects.all().filter(username=user_object).exists():
        return Profile.objects.all().get(username=user_object) not in Video.objects.all().get(id=video_id).recommendations.all()
    return False

@register.simple_tag
def has_messages(user_object):
    profile = Profile.objects.get(username=user_object)
    unreadmessages = profile.chats.filter(messages__read=False)
    if unreadmessages.exists():
        is_from_other_chatter = False
        for i in unreadmessages:
            if i.messages.latest("date_sent").sender != profile:
                is_from_other_chatter = True
        return is_from_other_chatter
    return False

@register.simple_tag
def unread_messages(user_object, chat_object):
    profile = Profile.objects.get(username=user_object)
    if chat_object.messages.exclude(sender=profile).filter(read=False).exists():
        return chat_object.messages.exclude(sender=profile).filter(read=False).count()
    return 0

@register.simple_tag
def notification_type(notification_object):
    if notification_object.comment_notification:
        return 1
    elif notification_object.update_notification:
        return 2
    elif notification_object.video_notification:
        return 3
    elif notification_object.milestone_notification:
        return 4
    elif notification_object.miscellaneous_notification:
        return 5
    else:
        return 0
    
@register.simple_tag
def following_eachother(user_object1, user_object2):
    profile1 = Profile.objects.get(username=user_object1)
    profile2 = Profile.objects.get(username=user_object2)
    return profile1.followers.contains(user_object2) and profile2.followers.contains(user_object1)

@register.simple_tag
def following_you(user_object1, user_object2):
    profile = Profile.objects.get(username=user_object1)
    return profile.followers.contains(user_object2)

@register.simple_tag
def other_chatter(chat, user_object):
    return Profile.objects.get(id=chat.members.exclude(id=Profile.objects.get(username=user_object).id).latest("date_made").id)

@register.simple_tag
def find(user_object):
    return Profile.objects.all().get(username=user_object)

@register.simple_tag
def is_in_creatorfund(profile):
    return Creator.objects.filter(profile=profile).exists()

@register.simple_tag
def has_profile(user_object):
    return Profile.objects.all().filter(username=user_object).exists()

@register.simple_tag
def has_replies(comment_pk):
    return Comment.objects.all().get(pk=comment_pk).replies.count() > 0

@register.simple_tag
def most_recent_video(profile_id):
    video = Profile.objects.all().get(id=profile_id).videos.all().order_by("-date_posted").exclude(unlisted=True).first()
    return Video.objects.all().filter(id=video.id)

@register.simple_tag
def most_liked_video(profile_id):
    video = Profile.objects.all().get(id=profile_id).videos.all().annotate(num_likes=Count('likes')).order_by("-num_likes").exclude(unlisted=True).first()
    return Video.objects.all().filter(id=video.id)

@register.simple_tag
def has_videos(profile_id):
    if Profile.objects.all().get(id=profile_id).videos.exclude(unlisted=True).count() == 0:
        return False
    return True

@register.simple_tag
def duration_to_hms(duration):
    return str(datetime.timedelta(seconds=round(duration))).removeprefix("0:")

@register.simple_tag
def reply_count(comment_pk):
    return Comment.objects.all().get(pk=comment_pk).replies.count()

@register.simple_tag
def video_nomination(user_object):
    return Profile.objects.all().get(username=user_object).nominated_video

@register.simple_tag
def profile_nomination(user_object):
    return Profile.objects.all().get(username=user_object).nominated_profile

@register.simple_tag
def video_object_as_queryset(video_object):
    return Video.objects.filter(id=video_object.id)

@register.simple_tag
def get_media_url():
    if not LOCAL:
        return "https://media.glomble.com"
    return "https://test-media.glomble.com"

# returns True or the timestamp for when it's possible again
@register.simple_tag
def can_appeal(ban):
    appeal_qs = ban.appeals
    now = timezone.now()

    if appeal_qs.exists():
        earliest_allowed = appeal_qs.order_by('-date_made').first().date_made+datetime.timedelta(days=30)
        if now > earliest_allowed:
            return True
        return earliest_allowed

    return True

@register.simple_tag
def is_developer(profile):
    developers = DEVELOPER_IDS
    return profile.id in developers

@register.simple_tag
def is_creator(profile):
    creator_id = 1
    return profile.username.id == creator_id