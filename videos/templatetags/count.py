from django import template
from reports.models import VideoReport, ProfileReport
from profiles.models import Profile
from creatorfund.models import Creator
from datetime import datetime, timedelta

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
        return Profile.objects.all().get(username=user).notifications.filter(read=False).count() > 0
    else:
        return False
    
@register.simple_tag
def can_recommend(user):
    if Profile.objects.all().filter(username=user).exists():
        return datetime.now().timestamp() > Profile.objects.all().get(username=user).last_recommend.timestamp() + 43200
    else:
        return False
    
@register.simple_tag
def has_messages(user):
    profile = Profile.objects.get(username=user)
    unreadmessages = profile.chats.filter(messages__read=False)
    if unreadmessages.exists():
        is_from_other_chatter = False
        for i in unreadmessages:
            if i.messages.latest("date_sent").sender != profile:
                is_from_other_chatter = True
        return is_from_other_chatter
    return False

@register.simple_tag
def notification_type(object):
    if object.comment_notification != None:
        return 1
    elif object.update_notification != None:
        return 2
    elif object.video_notification != None:
        return 3
    elif object.follow_notification != None:
        return 4
    else:
        return 0
    
@register.simple_tag
def following_eachother(user1, user2):
    profile1 = Profile.objects.get(username=user1)
    profile2 = Profile.objects.get(username=user2)
    return profile1.followers.contains(user2) and profile2.followers.contains(user1)

@register.simple_tag
def following_you(currentuser, otheruser):
    profile = Profile.objects.get(username=currentuser)
    return profile.followers.contains(otheruser)

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
