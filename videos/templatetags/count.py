from django import template
from reports.models import VideoReport, ProfileReport
from notifications.models import VideoNotification, CommentNotification, UpdateNotification
from profiles.models import Profile

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
        return VideoNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=user)], basenotification__read=False).count() > 0 or CommentNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=user)], basenotification__read=False).count() > 0 or UpdateNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=user)], basenotification__read=False).count() > 0
    else:
        return False

@register.simple_tag
def notification_type(object):
    if type(object) == CommentNotification:
        return 1
    elif type(object) == UpdateNotification:
        return 2
    elif type(object) == VideoNotification:
        return 3
    else:
        return 0

@register.simple_tag
def find(user):
    if not user:
        raise template.TemplateSyntaxError('`find` tag requires filters.')
    return Profile.objects.all().get(username=user)

@register.simple_tag
def has_profile(user):
    if not user:
        raise template.TemplateSyntaxError('`find` tag requires filters.')
    return Profile.objects.all().filter(username=user).exists()
