from profiles.models import Profile
from django.views.generic.list import ListView
from itertools import chain
from operator import attrgetter
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class NotificationsIndex(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "notifications/index.html"
    paginate_by = 25

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')

        profile = Profile.objects.all().get(username=self.request.user)
        
        profile_notifications = profile.basenotification_set.all()

        queryset = profile_notifications.filter(requires_action=True) | profile_notifications.filter(read=True) | profile_notifications.filter(read=False)

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
        
        profile_notifications.filter(read=False).update(read=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort_by = self.request.GET.get('sort-by')
        params = ""
        if sort_by:
            params += f"&sort-by={sort_by}"

        context["sort_by"] = sort_by
        context["params"] = params
        return context
    
    def test_func(self):
        return Profile.objects.all().filter(username=self.request.user).exists()