from .models import VideoNotification, UpdateNotification, BaseNotification
from profiles.models import Profile
from django.views.generic.list import ListView
from django.views.generic import View
from django.db.models import Count, Q
from django.shortcuts import render
from itertools import chain

class VideoNotificationsIndex(ListView):
    model = VideoNotification
    template_name = "notifications/index.html"
    paginate_by = 8

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryset = VideoNotification.objects.all().filter(notified_profiles__in=[Profile.objects.all().get(username=self.request.user)])

        if sort_by == 'date-desc':
            queryset = queryset.order_by('-date_made')
        elif sort_by == 'date-asc':
            queryset = queryset.order_by('date_made')
        elif sort_by == 'read':
            queryset = queryset.order_by('-date_made').exclude(basenotification__read=False)
        else:
            queryset = queryset.order_by('-date_made').exclude(basenotification__read=True)
        
        for i in queryset:
            for i in BaseNotification.objects.all().filter(notification=i):
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
