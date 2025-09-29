from django import template
from reports.models import VideoReport, ProfileReport, BugReport, Suggestion
from profiles.models import Profile
from creatorfund.models import Creator
from videos.models import Comment, Video
import datetime
from django.db.models import Count

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
def has_notifications(user):
    if Profile.objects.all().filter(username=user).exists():
        return Profile.objects.all().get(username=user).notifications.filter(read=False).count() > 0
    else:
        return False

@register.simple_tag
def can_recommend(video_id, user):
    if Profile.objects.all().filter(username=user).exists():
        return Profile.objects.all().get(username=user) not in Video.objects.all().get(id=video_id).recommendations.all()
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
def unread_messages(user, chat):
    profile = Profile.objects.get(username=user)
    if chat.messages.exclude(sender=profile).filter(read=False).exists():
        return chat.messages.exclude(sender=profile).filter(read=False).count()
    return 0

@register.simple_tag
def notification_type(object):
    if object.comment_notification != None:
        return 1
    elif object.update_notification != None:
        return 2
    elif object.video_notification != None:
        return 3
    elif object.milestone_notification != None:
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

@register.simple_tag
def has_replies(pk):
    return Comment.objects.all().get(pk=pk).replies.count() > 0

@register.simple_tag
def most_recent_video(id):
    video = Profile.objects.all().get(id=id).videos.all().order_by("-date_posted").exclude(unlisted=True).first()
    return Video.objects.all().filter(id=video.id)

@register.simple_tag
def most_liked_video(id):
    video = Profile.objects.all().get(id=id).videos.all().annotate(num_likes=Count('likes')).order_by("-num_likes").exclude(unlisted=True).first()
    return Video.objects.all().filter(id=video.id)

@register.simple_tag
def has_videos(id):
    if Profile.objects.all().get(id=id).videos.exclude(unlisted=True).count() == 0:
        return False
    return True

@register.simple_tag
def duration_to_hms(duration):
    return str(datetime.timedelta(seconds=round(duration))).removeprefix("0:")

@register.simple_tag
def reply_count(pk):
    return Comment.objects.all().get(pk=pk).replies.count()
