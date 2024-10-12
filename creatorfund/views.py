from django.shortcuts import render, reverse, redirect
from django.views.generic.edit import CreateView
from django.views.generic import FormView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Creator, CreatorFund, CreatorGroup
from profiles.models import Profile
from videos.models import Video, Comment
import random
from .forms import UpdateCreatorForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

def sort_videos_by_earnings(creator):
    videos = Video.objects.filter(uploader=creator.profile)

    video_percentages = []

    for video in videos:
        video_views = video.views.count()
        video_likes = video.likes.count()
        video_dislikes = video.dislikes.count()
        total_comments = Comment.objects.filter(post=video).count()

        if video_likes + video_dislikes > 0:
            like_dislike_ratio = video_likes / (video_likes + video_dislikes)
        else:
            like_dislike_ratio = 1

        video_earnings = CreatorFund.objects.get(pk=1).available_money % (
            video_views * 0.15 +
            video_likes * 0.25 +
            like_dislike_ratio * 0.15 +
            total_comments * 0.1
        )

        video_earnings = round(video_earnings, 4)

        video_percentages.append((video, video_earnings))

    videos_sorted = sorted(video_percentages, key=lambda x: x[1], reverse=True)

    return videos_sorted


def get_percentage_share(creator):
    creators = Creator.objects.all()

    creator_scores = {}

    for i in creators:
        profile = i.profile
        follower_count = profile.followers.count()

        videos = Video.objects.filter(uploader=profile)
        total_video_views = sum([video.views.count() for video in videos])
        total_video_likes = sum([video.likes.count() for video in videos])
        total_video_dislikes = sum([video.dislikes.count() for video in videos])

        comments = Comment.objects.filter(commenter=profile)
        total_comments = Comment.objects.filter(post__uploader=profile).count()
        total_comment_likes = sum([comment.likes.count() for comment in comments])

        if total_video_likes + total_video_dislikes > 0:
            like_dislike_ratio = total_video_likes / (total_video_likes + total_video_dislikes)
        else:
            like_dislike_ratio = 1

        engagement_score = (
            follower_count * 0.3 +
            total_video_views * 0.15 +
            total_video_likes * 0.25 +
            total_comment_likes * 0.05 +
            like_dislike_ratio * 0.15 +
            total_comments * 0.1
        )

        creator_scores[profile] = engagement_score

    total_score = sum(creator_scores.values())
    
    if total_score == 0:
        return {profile: 0 for profile in creators}

    profile_percentages = {
        profile: (score / total_score) * 100
        for profile, score in creator_scores.items()
    }

    creator_profile = creator.profile
    creator_percentage = profile_percentages.get(creator_profile, 0)

    return creator_percentage, profile_percentages


class CreateFundingProfile(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Creator
    fields = ['paypal_email']
    template_name = 'creatorfund/createprofile.html'
    is_valid = None
    
    def form_valid(self, form):

        profile = Profile.objects.get(username=self.request.user)
        form.instance.id = profile.id
        form.instance.profile = profile
        form.instance.creator_fund = CreatorFund.objects.get(pk=1)
        form.save()
        form.instance.percentage_share = get_percentage_share(form.instance)[0]

        return super().form_valid(form)

    def form_invalid(self, form):
        try:
            Creator.objects.all().filter(id=self.object.id).delete()
        except:
            pass

        return super().form_invalid(form)
    
    def test_func(self):
        if Profile.objects.all().filter(username=self.request.user).exists():
            return not Creator.objects.all().filter(profile=Profile.objects.all().get(username=self.request.user)).exists()
        else:
            return False
        
    def get_success_url(self):
        return reverse('detail-funding-profile')
    
class CreateFundgroup(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = CreatorGroup
    fields = ['name']
    template_name = 'creatorfund/create_fund_group.html'
    is_valid = None
    
    def form_valid(self, form):
        form.instance.profile = Profile.objects.get(username=self.request.user)

        unique = False
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        out = random.choice(chars)
        
        while not unique:
            for i in range(11):
                out += random.choice(chars)
            if not CreatorGroup.objects.filter(id=out).exists():
                unique = True
            else:
                out = out[:1]

        form.instance.id = out

        return super().form_valid(form)

    def form_invalid(self, form):
        Creator.objects.all().filter(pk=self.object.pk).delete()

        return super().form_invalid(form)
    
    def test_func(self):
        if Profile.objects.all().filter(username=self.request.user).exists():
            profile = Profile.objects.all().get(username=self.request.user)
            return CreatorGroup.objects.filter(members__in=Creator.objects.get(profile=profile))
        else:
            return False
    
class DetailFundingProfile(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        if Profile.objects.all().filter(username=self.request.user).exists():
            return (Creator.objects.all().filter(profile=Profile.objects.all().get(username=self.request.user)).exists() and
            Creator.objects.all().get(profile=Profile.objects.all().get(username=self.request.user)).profile.username == self.request.user)
        else:
            return False

    def get(self, request, *args, **kwargs):
        funding_profile = Creator.objects.all().get(profile=Profile.objects.all().get(username=self.request.user))
        estimated_income = (funding_profile.percentage_share * CreatorFund.objects.get(pk=1).available_money) / 100
        next_payout = CreatorFund.objects.get(pk=1).next_payout
        ordered_videos = sort_videos_by_earnings(funding_profile)

        context = {
            'funding_profile': funding_profile,
            'estimated_income': estimated_income,
            'next_payout': next_payout,
            'ordered_videos': ordered_videos,
        }

        return render(request, 'creatorfund/detailcreator.html', context)
    
class DetailFundGroup(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        if Profile.objects.all().filter(username=self.request.user).exists():
            return not Creator.objects.all().filter(profile=Profile.objects.all().get(username=self.request.user)).exists()
        else:
            return False

    def get(self, request, *args, **kwargs):
        content_creator = Creator.objects.all().get(profile=Profile.objects.all().get(username=self.request.user))
        funding_group = content_creator.creator_fund
        is_funding_group_creator = Creator.objects.all().get(profile=Profile.objects.all().get(username=self.request.user)) == funding_group.group_creator

        context = {
            'funding_profile': funding_group,
            'creator': is_funding_group_creator,
        }

        return render(request, 'creatorfund/detail_fund_group.html', context)
    
def leave_creator_fund(request):
    if Creator.objects.filter(profile__username=request.user).exists():
        Creator.objects.get(profile__username=request.user).delete()
    return redirect('profile-page')

@login_required
def update_creator_info(request):
    user = request.user
    has_profile = Profile.objects.filter(username=user).exists()
    if has_profile:
        creator = Creator.objects.get(profile=Profile.objects.get(username=user))
        form = UpdateCreatorForm(request.POST, instance=creator)
    else:
        return redirect('index')
    
    if request.method == "POST":
        creator = Creator.objects.get(profile=Profile.objects.get(username=user))
        if form.is_valid():
            form.save()
            return redirect('detail-funding-profile')
    
    context = {
        'form': form
    }
    return render(request, "creatorfund/updatecreator.html", context)