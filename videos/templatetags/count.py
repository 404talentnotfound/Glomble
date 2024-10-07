from django import template
from reports.models import VideoReport, ProfileReport
from notifications.models import VideoNotification
from profiles.models import Profile

register = template.Library()

@register.simple_tag
def V_reports():
    return VideoReport.objects.all().count() > 0

@register.simple_tag
def P_reports():
    return ProfileReport.objects.all().count() > 0

@register.simple_tag
def V_Notifications(user):
    if Profile.objects.all().filter(username=user).exists():
        return VideoNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=user)], basenotification__read=False).count() > 0
    else:
        return False

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
