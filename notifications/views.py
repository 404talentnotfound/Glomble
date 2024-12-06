from profiles.models import Profile
from .models import BaseNotification
from django.views.generic.list import ListView
from itertools import chain
from operator import attrgetter

class NotificationsIndex(ListView):
    template_name = "notifications/index.html"
    paginate_by = 15

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