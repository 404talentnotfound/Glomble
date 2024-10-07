from django import template
from profiles.models import Profile

register = template.Library()

@register.simple_tag
def find(user):
    if not user:
        raise template.TemplateSyntaxError('`find` tag requires filters.')
    return Profile.objects.all().get(username=user)