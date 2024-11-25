from .models import VideoNotification, UpdateNotification, BaseNotification, CommentNotification, FollowNotification
from profiles.models import Profile
from django.views.generic.list import ListView
from django.views.generic import View
from django.db.models import Count, Q
from django.shortcuts import render
from itertools import chain
from operator import attrgetter

class NotificationsIndex(ListView):
    template_name = "notifications/index.html"
    paginate_by = 25

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryset = list(chain(Profile.objects.all().get(username=self.request.user).notifications.exclude(read=False), Profile.objects.all().get(username=self.request.user).notifications.exclude(read=True)))

        if sort_by == 'date-desc':
            queryset = sorted(
                queryset,
                key=attrgetter('date_notified'),
                reverse=True
            )
        elif sort_by == 'date-asc':
            queryset = sorted(
                queryset,
                key=attrgetter('date_notified'),
            )
        else:
            queryset = sorted(
                queryset,
                key=attrgetter('date_notified'),
                reverse=True
            )
        
        for i in queryset:
            i.read = True
            i.save()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort-by')
        return context
    
class VideoNotificationSearch(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('query')
        video_notification_list = VideoNotification.objects.filter(
        	Q(message__icontains=query)
        ).filter(notified_profiles__in=[Profile.objects.all().get(username=self.request.user)])
    
        context = {
        	'video_notification_list': video_notification_list
        }
    

        return render(request, 'notifications/search.html', context)

