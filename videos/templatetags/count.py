from django import template
from reports.models import VideoReport, ProfileReport
from notifications.models import VideoNotification, CommentNotification, UpdateNotification, FollowNotification, LikeNotification
from profiles.models import Profile, Chat
from creatorfund.models import Creator

register = template.Library()

@register.simple_tag
def V_reports():
    return VideoReport.objects.all().count() > 0

@register.simple_tag
def P_reports():
    return ProfileReport.objects.all().count() > 0

@register.simple_tag
def has_notifications(user):
    if Profile.objects.all().filter(username=user).exists():
        return (VideoNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=user)], basenotification__read=False).count() > 0 or
                CommentNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=user)], basenotification__read=False).count() > 0 or
                UpdateNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=user)], basenotification__read=False).count() > 0 or
                LikeNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=user)], basenotification__read=False).count() > 0 or
                FollowNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=user)], basenotification__read=False).count() > 0)
    else:
        return False
    
@register.simple_tag
def has_messages(user):
    profile = Profile.objects.get(username=user)
    unreadmessages = Chat.objects.filter(members__in=[profile]).filter(messages__read=False)
    if unreadmessages.exists():
        for i in unreadmessages:
            return i.messages.latest("date_sent").sender != profile
    return False

@register.simple_tag
def notification_type(object):
    if type(object) == CommentNotification:
        return 1
    elif type(object) == UpdateNotification:
        return 2
    elif type(object) == VideoNotification:
        return 3
    elif type(object) == LikeNotification:
        return 4
    elif type(object) == FollowNotification:
        return 5
    else:
        return 0
    
@register.simple_tag
def following_eachother(user1, user2):
    profile1 = Profile.objects.get(username=user1)
    profile2 = Profile.objects.get(username=user2)
    return profile1.followers.contains(user2) and profile2.followers.contains(user1)

@register.simple_tag
def other_chatter(chat, user):
    return Profile.objects.get(id=chat.members.exclude(id=Profile.objects.get(username=user).id).latest("date_made").id)

@register.simple_tag
def find(user):
    return Profile.objects.all().get(username=user)

@register.simple_tag
def is_in_creatorfund(profile):
    return Creator.objects.filter(profile=profile).exists()

@register.simple_tag
def has_profile(user):
    return Profile.objects.all().filter(username=user).exists()
