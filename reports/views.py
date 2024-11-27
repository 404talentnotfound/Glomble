from django.shortcuts import render, reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import VideoReport, ProfileReport, BugReport, Suggestion
from profiles.models import Profile
from videos.models import Video
from django.core.cache import cache
from datetime import datetime, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

@staff_member_required
def choice_page(request):
    username = request.GET.get('username', request.user)
    profile = Profile.objects.get(username=username)
    v_count = VideoReport.objects.all().count()
    p_count = ProfileReport.objects.all().count()
    b_count = BugReport.objects.all().count()
    s_count = Suggestion.objects.all().count()
    context = {
        'profile': profile,
        'v_count': v_count,
        'p_count': p_count,
        'b_count': b_count,
        's_count': s_count,
    }
    return render(request, 'reports/choice_page.html', context)

class VideoReportIndex(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'reports/videos_index.html'
    context_object_name = 'reports'
    paginate_by = 9

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryset = VideoReport.objects.all()

        if sort_by == 'date-desc':
            queryset = queryset.order_by('-date_sent')
        elif sort_by == 'date-asc':
            queryset = queryset.order_by('date_sent')
        else:
            queryset = queryset.order_by('-date_sent')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort-by')
        return context
    
    def test_func(self):
        return self.request.user.is_superuser

class DeleteVideoReport(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = VideoReport
    template_name = 'reports/delete_report.html'
    def get_redirect_url(self):
        return reverse('video-report-detail', kwargs={'pk': self.object.pk})

    def get_success_url(self):
        post = VideoReport.objects.all().get(pk=self.kwargs['pk']).post
        VideoReport.objects.all().filter(post=post).delete()

        return reverse('video-report-index')
    
    def test_func(self):
        return self.request.user.is_superuser
    
class ReportVideo(LoginRequiredMixin, CreateView):
    model = VideoReport
    fields = ['brief_summary', 'reasoning']
    template_name = 'reports/create_video_report.html'
    is_valid = None
    
    def form_valid(self, form):
        cooldown_valid = True
        last_report_time = cache.get(f"last_video_report_{self.request.user.id}")

        if last_report_time is not None and datetime.now() < last_report_time + timedelta(minutes=2):
            form.add_error(None, "You can only send one video report every 2 minutes.")
            cooldown_valid = False
            return super().form_invalid(form)

        form.instance.reporter = self.request.user
        try:
            form.instance.post = Video.objects.all().get(id=self.kwargs['id'])
            context = {
                'post': form.instance.post,
            }
        except:
            form.add_error(None, "Invalid video, please try again later.")
            return super().form_invalid(form)

        if cooldown_valid and form.instance.post != None:
            cache.set(f"last_video_report_{self.request.user.id}", datetime.now(), timeout=None)
            form.save()
            return render(self.request, 'reports/video_report_sent.html', context)
        else:
            return super().form_invalid(form)

    def form_invalid(self, form):
        VideoReport.objects.all().filter(pk=self.object.pk).delete()

        return super().form_invalid(form)

class DetailVideoReport(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        e = self.kwargs['pk']
        pen = VideoReport.objects.get(pk=e)
        hi = VideoReport.objects.get(pk=e).reporter
        thing = Profile.objects.get(username=hi).id

        context = {
            'e': e,
            'thing': thing,
            'report': pen,
        }

        return render(request, 'reports/detail_video_report.html', context)
    
class ProfileReportIndex(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'reports/profiles_index.html'
    context_object_name = 'reports'
    paginate_by = 9

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryset = ProfileReport.objects.all()

        if sort_by == 'date-desc':
            queryset = queryset.order_by('-date_sent')
        elif sort_by == 'date-asc':
            queryset = queryset.order_by('date_sent')
        else:
            queryset = queryset.order_by('-date_sent')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort-by')
        return context
    
    def test_func(self):
        return self.request.user.is_superuser

class DeleteProfileReport(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ProfileReport
    template_name = 'reports/delete_report.html'
    def get_redirect_url(self):
        return reverse('report-profile-detail', kwargs={'pk': self.object.pk})

    def get_success_url(self):
        profile = ProfileReport.objects.all().get(pk=self.object.pk).profile

        ProfileReport.objects.all().filter(profile=profile).delete()
        
        return reverse('profile-report-index')
    
    def test_func(self):
        return self.request.user.is_superuser
    
class ReportProfile(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ProfileReport
    fields = ['brief_summary', 'reasoning']
    template_name = 'reports/create_profile_report.html'
    is_valid = None
    
    def form_valid(self, form):
        cooldown_valid = True
        last_report_time = cache.get(f"last_profile_report_{self.request.user.id}")

        if last_report_time is not None and datetime.now() < last_report_time + timedelta(minutes=2):
            form.add_error(None, "You can only send one profile report every 2 minutes.")
            cooldown_valid = False
            return super().form_invalid(form)

        form.instance.reporter = self.request.user
        try:
            form.instance.profile = Profile.objects.all().get(id=self.kwargs['id'])
            context = {
                'post': form.instance.profile,
            }
        except:
            form.add_error(None, "Invalid profile, please try again later.")
            return super().form_invalid(form)

        if cooldown_valid and form.instance.profile != None:
            cache.set(f"last_profile_report_{self.request.user.id}", datetime.now(), timeout=None)
            form.save()
            return render(self.request, 'reports/profile_report_sent.html', context)
        else:
            return super().form_invalid(form)

    def form_invalid(self, form):
        ProfileReport.objects.all().filter(pk=self.object.pk).delete()

        return super().form_invalid(form)
    
    def test_func(self):
        return Profile.objects.all().get(id=self.kwargs['id']) != Profile.objects.all().get(username=self.request.user)

class DetailProfileReport(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        e = self.kwargs['pk']
        pen = ProfileReport.objects.get(pk=e)
        hi = ProfileReport.objects.get(pk=e).reporter
        thing = Profile.objects.get(username=hi).id

        context = {
            'e': e,
            'thing': thing,
            'report': pen,
        }

        return render(request, 'reports/detail_profile_report.html', context)

class BugReportIndex(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'reports/bugs_index.html'
    context_object_name = 'reports'
    paginate_by = 9

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryset = BugReport.objects.all()

        if sort_by == 'date-desc':
            queryset = queryset.order_by('-date_sent')
        elif sort_by == 'date-asc':
            queryset = queryset.order_by('date_sent')
        else:
            queryset = queryset.order_by('-date_sent')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort-by')
        return context
    
    def test_func(self):
        return self.request.user.is_superuser

class DeleteBugReport(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = BugReport
    template_name = 'reports/delete_report.html'
    def get_redirect_url(self):
        return reverse('report-bug-detail', kwargs={'pk': self.object.pk})
    
    def post(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):        
        return reverse('bug-report-index')
    
    def test_func(self):
        return self.request.user.is_superuser
    
class ReportBug(LoginRequiredMixin, CreateView):
    model = BugReport
    fields = ['brief_summary', 'explanation']
    template_name = 'reports/create_bug_report.html'
    is_valid = None
    
    def form_valid(self, form):
        cooldown_valid = True
        last_report_time = cache.get(f"last_bug_report_{self.request.user.id}")

        if last_report_time is not None and datetime.now() < last_report_time + timedelta(minutes=2):
            form.add_error(None, "You can only send one bug report every 2 minutes.")
            cooldown_valid = False
            return super().form_invalid(form)

        form.instance.reporter = self.request.user

        cache.set(f"last_bug_report_{self.request.user.id}", datetime.now(), timeout=None)
        form.save()
        return render(self.request, 'reports/bug_report_sent.html')

    def form_invalid(self, form):
        BugReport.objects.all().filter(pk=self.object.pk).delete()

        return super().form_invalid(form)

class DetailBugReport(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        e = self.kwargs['pk']
        pen = BugReport.objects.get(pk=e)
        hi = BugReport.objects.get(pk=e).reporter
        thing = Profile.objects.get(username=hi).id

        context = {
            'e': e,
            'thing': thing,
            'report': pen,
        }

        return render(request, 'reports/detail_bug_report.html', context)
    
class SuggestionIndex(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'reports/suggestions_index.html'
    context_object_name = 'reports'
    paginate_by = 9

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryset = Suggestion.objects.all()

        if sort_by == 'date-desc':
            queryset = queryset.order_by('-date_sent')
        elif sort_by == 'date-asc':
            queryset = queryset.order_by('date_sent')
        else:
            queryset = queryset.order_by('-date_sent')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort-by')
        return context
    
    def test_func(self):
        return self.request.user.is_superuser

class DeleteSuggestion(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Suggestion
    template_name = 'reports/delete_report.html'
    def get_redirect_url(self):
        return reverse('suggestion-detail', kwargs={'pk': self.object.pk})
    
    def post(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):        
        return reverse('suggestion-index')
    
    def test_func(self):
        return self.request.user.is_superuser
    
class Suggest(LoginRequiredMixin, CreateView):
    model = Suggestion
    fields = ['brief_summary', 'explanation']
    template_name = 'reports/create_suggestion.html'
    is_valid = None
    
    def form_valid(self, form):
        last_report_time = cache.get(f"last_suggestion_{self.request.user.id}")

        if last_report_time is not None and datetime.now() < last_report_time + timedelta(minutes=2):
            form.add_error(None, "You can only send one bug report every 2 minutes.")
            return super().form_invalid(form)

        form.instance.reporter = self.request.user

        cache.set(f"last_suggestion_{self.request.user.id}", datetime.now(), timeout=None)
        form.save()
        return render(self.request, 'reports/suggestion_sent.html')

    def form_invalid(self, form):
        Suggestion.objects.all().filter(pk=self.object.pk).delete()

        return super().form_invalid(form)

class DetailSuggestion(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        e = self.kwargs['pk']
        pen = Suggestion.objects.get(pk=e)
        hi = Suggestion.objects.get(pk=e).reporter
        thing = Profile.objects.get(username=hi).id

        context = {
            'e': e,
            'thing': thing,
            'report': pen,
        }

        return render(request, 'reports/detail_suggestion.html', context)
        