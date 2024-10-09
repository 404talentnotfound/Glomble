from .models import VideoNotification, UpdateNotification, BaseNotification, CommentNotification
from profiles.models import Profile
from django.views.generic.list import ListView
from django.views.generic import View
from django.db.models import Count, Q
from django.shortcuts import render
from itertools import chain
from operator import attrgetter

class VideoNotificationsIndex(ListView):
    model = VideoNotification
    template_name = "notifications/index.html"
    paginate_by = 8

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryset = list(chain(VideoNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=self.request.user)]), CommentNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=self.request.user)]), UpdateNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=self.request.user)])))
        
        shouldnt_read = False

        if sort_by == 'date-desc':
            queryset = sorted(
                queryset,
                key=attrgetter('date_made'),
                reverse=True
            )
        elif sort_by == 'date-asc':
            queryset = sorted(
                queryset,
                key=attrgetter('date_made'),
                reverse=True
            )
        elif sort_by == 'read':
            queryset = list(chain(VideoNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=self.request.user)]).exclude(basenotification__read=False), CommentNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=self.request.user)]).exclude(basenotification__read=False), UpdateNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=self.request.user)]).exclude(basenotification__read=False)))
            queryset = sorted(
                queryset,
                key=attrgetter('date_made'),
                reverse=True
            )
            shouldnt_read = True
        else:
            queryset = list(chain(VideoNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=self.request.user)]).exclude(basenotification__read=True), CommentNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=self.request.user)]).exclude(basenotification__read=True), UpdateNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=self.request.user)]).exclude(basenotification__read=True)))
            queryset = sorted(
                queryset,
                key=attrgetter('date_made'),
                reverse=True
            )
        
        if not shouldnt_read:
            for i in queryset:
                if type(i) == VideoNotification:
                    for i in BaseNotification.objects.all().filter(video_notification=i):
                        i.read = True
                        i.save()
                elif type(i) == CommentNotification:
                    for i in BaseNotification.objects.all().filter(comment_notification=i):
                        i.read = True
                        i.save()
                elif type(i) == UpdateNotification:
                    for i in BaseNotification.objects.all().filter(update_notification=i):
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
