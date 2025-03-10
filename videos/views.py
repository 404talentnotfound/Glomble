from django.shortcuts import render, reverse, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from .models import Video, Comment
from django.db.models import Q, Count
from moviepy.video.io.VideoFileClip import VideoFileClip
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from profiles.models import Profile
from .forms import CommentForm, ReplyForm
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core import serializers
from datetime import datetime, timedelta
import tempfile
import os
import random
from Glomble.pc_prod import *
import subprocess
from django.shortcuts import render
from notifications.models import MilestoneNotification

def get_recommended_videos(request, category):
    videos = random.sample(list(Video.objects.all().filter(category=category)),3)
    rendered_html = render(request, 'videos/recommended_videos.html', {'recommended_videos': videos})
    return JsonResponse({"html": rendered_html.content.decode('utf-8')})

def update_video_view_count(request, id):
    viewed = False
    if not request.user.is_anonymous:
        if not Video.objects.get(id=id).views.all().filter(username=request.user).exists():
            key = f"user:{User.objects.all().get(username=request.user)}:video:{id}"

            start_time = cache.get(key)
            if start_time is None:
                start_time = timezone.now().timestamp()
                cache.set(key, start_time, timeout=None)

            elapsed_time = timezone.now().timestamp() - start_time
            if elapsed_time >= 0.3 * Video.objects.get(id=id).duration or elapsed_time >= 5:
                if not cache.get(f"{key}:viewed"):
                    video = Video.objects.get(id=id)
                    video.views.add(User.objects.all().get(id=request.user.id))

                    profile = Profile.objects.get(username=request.user)

                    profile.watched_videos.add(video)

                    cache.set(f"{key}:viewed", 1, timeout=None)
                    viewed = True
        else:
            viewed = True
    else:
        viewed = True

    view_count = Video.objects.get(id=id).views.count()
    return JsonResponse({"view_count": view_count, "viewed": viewed})

def update_video_recommendation_count(request, id):
    recommendation_count = Video.objects.get(id=id).recommendations
    return JsonResponse({"recommendation_count": recommendation_count})

def update_video_like_count(request, id):
    like_count = Video.objects.get(id=id).likes.count()
    dislike_count = Video.objects.get(id=id).dislikes.count()
    return JsonResponse({"like_count": like_count, "dislike_count": dislike_count})

def update_comments_like_count(request, id):
    for comment in Video.objects.get(id=id).comments.all():
        like_count = comment.likes.count()
        dislike_count = comment.dislikes.count()
        return JsonResponse({"like_count": like_count, "dislike_count": dislike_count, "pk_comment": comment.pk})

def handler500(request, exception, template_name="500.html"):
    response = render(template_name)
    response.status_code = 500
    return response

def redirect_index(request):
    return redirect('/')

def redirect_video(request, id):
    return redirect(f'{reverse("video-detail", kwargs={"id": id})}')

def mcdonalds(request):
    return redirect('https://mcdonalds.com')

class Index(ListView):
    model = Video
    template_name = 'videos/index.html'
    context_object_name = 'videos'
    paginate_by = 54

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        category = self.request.GET.get('category')
        queryset = Video.objects.all().exclude(unlisted=True).exclude(uploader__shadowbanned=True)

        if category == 'memes':
            queryset = queryset.filter(category="Memes")
        elif category == 'gaming':
            queryset = queryset.filter(category="Gaming")
        elif category == 'education':
            queryset = queryset.filter(category="Education")
        elif category == 'animation':
            queryset = queryset.filter(category="Animation")
        elif category == 'entertainment':
            queryset = queryset.filter(category="Entertainment")
        elif category == 'music':
            queryset = queryset.filter(category="Music")
        elif category == 'discussion':
            queryset = queryset.filter(category="Discussion")
        elif category == 'miscellaneous':
            queryset = queryset.filter(category="Miscellaneous")

        if sort_by == 'newest':
            queryset = queryset.order_by('-date_posted')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('date_posted')
        elif sort_by == 'likes':
            queryset = queryset.annotate(num_likes=Count('likes')).order_by('-num_likes')
        elif sort_by == 'views':
            queryset = queryset.annotate(num_views=Count('views')).order_by('-num_views')
        elif sort_by == "recommended":
            queryset = queryset.annotate(num_likes=Count('likes')).order_by("-recommendations", '-num_likes')
        else:
            queryset = queryset.annotate(num_likes=Count('likes')).order_by("-recommendations", '-num_likes')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort-by')
        context['category'] = self.request.GET.get('category')
        return context

class CreateVideo(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Video
    fields = ['title', 'notification_message', 'description', 'category', 'video_file', 'thumbnail', 'unlisted', 'push_notification']
    template_name = 'videos/create_video.html'
    redirect_field_name = reverse_lazy('video-create')
    is_valid = None

    def test_func(self):
        return Profile.objects.all().filter(username=self.request.user).exists()

    def form_valid(self, form):
        last_upload_time = cache.get(f"last_upload_{self.request.user.id}")

        if last_upload_time and datetime.now() < last_upload_time + timedelta(minutes=2):
            form.add_error(None, "You can only upload one video every 2 minutes.")
            return self.form_invalid(form)

        form.instance.uploader = Profile.objects.get(username=self.request.user)

        unique = False
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        video_id = random.choice(chars)

        while not unique:
            video_id += "".join(random.choice(chars) for _ in range(10))
            if not Video.objects.filter(id=video_id).exists():
                unique = True
            else:
                video_id = video_id[:1]

        form.instance.id = video_id

        uploaded_video = self.request.FILES['video_file']
        if not 1024 < uploaded_video.size < 5000000000:
            form.add_error(None, "The video size must be between 1kb and 5gb.")
            return self.form_invalid(form)
        
        temp_video_file = tempfile.NamedTemporaryFile(delete=False)
        temp_video_file.write(uploaded_video.read())
        
        try:
            uploaded_thumbnail = self.request.FILES['thumbnail']
            if not 1024 < uploaded_thumbnail.size < 10000000:
                form.add_error(None, "The thumbnail size must be between 1kb and 10mb.")
                return self.form_invalid(form)
            temp_thumbnail_file = tempfile.NamedTemporaryFile(delete=False)
            temp_thumbnail_file.write(uploaded_thumbnail.read())
        except:
            uploaded_thumbnail = False

        try:
            vid = VideoFileClip(temp_video_file.name)

            if vid.duration > 7200 or vid.duration < 1:
                form.add_error(None, "The video duration must be between 1 second and 2 hours.")
                return self.form_invalid(form)

            video_filename = os.path.join(BASE_DIR, f"media/uploads/video_files/{video_id}.mp4")
            try:
                gif = False
                if uploaded_thumbnail.name[-3:] != "gif":
                        thumbnail_filename = os.path.join(BASE_DIR, f"media/uploads/thumbnails/{video_id}.png")
                else:
                        gif = True
                        thumbnail_filename = os.path.join(BASE_DIR, f"media/uploads/thumbnails/{video_id}.gif")
            except:
                gif = False
                thumbnail_filename = os.path.join(BASE_DIR, f"media/uploads/thumbnails/{video_id}.png")

            subprocess.run(
                f"sudo ffmpeg -i {temp_video_file.name} -vf scale=1920:-2 -c:v libx264 -crf 28 -c:a copy -preset fast {video_filename}",
                shell=True,
                check=True,
            )

            if uploaded_thumbnail:
                subprocess.run(
                    f"sudo ffmpeg -i {temp_thumbnail_file.name} -vf scale=1280:-2 {thumbnail_filename}",
                    shell=True,
                    check=True,
                )
                if not gif:
                    form.instance.thumbnail.name = f"{video_id}.png"
                else:
                    form.instance.thumbnail.name = f"{video_id}.gif"
            else:
                form.instance.thumbnail.name = f"media/uploads/thumbnails/{video_id}.png"
                vid.save_frame(thumbnail_filename, t=0)

            form.instance.video_file.name = f"{video_id}.mp4"

            form.instance.duration = vid.duration
            cache.set(f"last_upload_{self.request.user.id}", datetime.now(), timeout=None)

            return super().form_valid(form)

        except:
            form.add_error(None, f"An error occurred during processing")
            return self.form_invalid(form)

        finally:
            try:
                os.remove(temp_video_file.name)
            except OSError:
                pass

    def form_invalid(self, form):
        if hasattr(self, 'object') and self.object:
            try:
                os.remove(f"media/uploads/video_files/{self.object.id}.mp4")
                os.remove(f"media/uploads/thumbnails/{self.object.id}.png")
            except OSError:
                pass
            self.object.delete()

        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

class DetailVideo(DetailView):
    def get(self, request, *args, **kwargs):
        e = self.kwargs['id']
        form = CommentForm()
        replyform = ReplyForm()
        pen = Video.objects.get(id=e)
        desclen = None
        pre = None
        readmore = None
        if pen.description is not None:
            has_desc = True
            desclen = len(pen.description)
            pre = pen.description[:25]
            readmore = pen.description[25:]
        else:
            has_desc = False

        comments = pen.comments.all().filter(replying_to=None).annotate(num_likes=Count('likes')).order_by('-num_likes')
        comment_count = pen.comments.count()

        replies = pen.comments.all().exclude(replying_to=None).order_by('date_posted')

        is_following = False

        if pen.uploader.followers.all().count() == 0:
            is_following = False

        for follower in pen.uploader.followers.all():
            if follower == request.user:
                is_following = True
                break
            else:
                is_following = False

        context = {
            'e': e,
            'post': pen,
            'form': form,
            'replyform': replyform,
            'comments': comments,
            'comment_amount': comment_count,
            'pre': pre,
            'readmore': readmore,
            'desclen': desclen,
            'has': has_desc,
            'is_following': is_following,
            'replies': replies
        }

        return render(request, 'videos/detail_video.html', context)

    def post(self, request, *args, **kwargs):
        e = self.kwargs['id']
        pen = Video.objects.get(id=e)
        form = CommentForm(request.POST)
        replyform = ReplyForm(request.POST)

        desclen = None
        pre = None
        readmore = None

        if pen.description is not None:
            has_desc = True
            desclen = len(pen.description)
            pre = pen.description[:25]
            readmore = pen.description[25:]
        else:
            has_desc = False

        is_following = False

        if pen.uploader.followers.all().count() == 0:
            is_following = False

        for follower in pen.uploader.followers.all():
            if follower == request.user:
                is_following = True
                break
            else:
                is_following = False

        comments = pen.comments.all().filter(replying_to=None).annotate(num_likes=Count('likes')).order_by('-num_likes')
        comment_count = pen.comments.count()

        replies = pen.comments.all().exclude(replying_to=None).order_by('date_posted')

        context = {
            'e': e,
            'post': pen,
            'form': CommentForm(),
            'replyform': ReplyForm(),
            'comments': comments,
            'pre': pre,
            'readmore': readmore,
            'desclen': desclen,
            'has': has_desc,
            'is_following': is_following,
            'comment_amount': comment_count,
            'replies': replies
        }
        
        form_type = request.POST.get("form_type")

        last_comment_time = cache.get(f"last_comment_{self.request.user.id}")

        if last_comment_time and datetime.now() < last_comment_time + timedelta(seconds=10):
            if form_type == "comment":
                form.add_error(None, "You can only upload one comment every 10 seconds")
            else:
                replyform.add_error(None, "You can only upload one comment every 10 seconds")
            return render(request, 'videos/detail_video.html', context)

        elif form_type == "comment" and form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.commenter = Profile.objects.get(username=request.user)
            new_comment.post = pen
            new_comment.save()

            pen.comments.add(new_comment)

            cache.set(f"last_comment_{self.request.user.id}", datetime.now(), timeout=None)
            return redirect(f'{reverse("video-detail", kwargs={"id": e})}')

        elif form_type == "reply" and replyform.is_valid():
            new_reply = replyform.save(commit=False)
            new_reply.replying_to = Comment.objects.get(id=int(request.POST.get("comment_id")))
            new_reply.commenter = Profile.objects.get(username=request.user)
            new_reply.post = pen
            new_reply.save()

            Comment.objects.get(id=int(request.POST.get("comment_id"))).replies.add(new_reply)
            pen.comments.add(new_reply)

            cache.set(f"last_comment_{self.request.user.id}", datetime.now(), timeout=None)
            return redirect(f'{reverse("video-detail", kwargs={"id": e})}')

        return render(request, 'videos/detail_video.html', context)

class UpdateVideo(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Video
    slug_url_kwarg = "id"
    slug_field = "id"
    fields = ['title', 'description', 'category', 'unlisted']
    template_name = 'videos/update_video.html'
        
    def get_success_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})
    
    def get_redirect_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

    def test_func(self):
        video = self.get_object()
        return self.request.user == video.uploader.username or self.request.user.is_superuser

class DeleteVideo(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Video
    slug_url_kwarg = "id"
    slug_field = "id"
    template_name = 'videos/delete_video.html'
    def get_redirect_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

    def get_success_url(self):
        return reverse('index')
    
    def test_func(self):
        video = self.get_object()
        return self.request.user == video.uploader.username or self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

class AddLike(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_redirect_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']
        video = Video.objects.get(id=hi)
        is_dislike = False
        for dislike in video.dislikes.all():
            if dislike == request.user:
                is_dislike = True
                break
        if is_dislike:
            video.dislikes.remove(request.user)
        is_like = False
        for like in video.likes.all():
            if like == request.user:
                is_like = True
                break
        if not is_like:
            video.likes.add(request.user)

        if is_like:
            video.likes.remove(request.user)

        likes_count = video.likes.count()

        dislikes_count = video.dislikes.count()
        
        return JsonResponse({'likes_count': likes_count, 'liked': not is_like, 'dislikes_count': dislikes_count, 'disliked': is_dislike})
    
    def test_func(self):
        return Profile.objects.all().filter(username=self.request.user).exists()
        
class Dislike(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_redirect_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']
        video = Video.objects.get(id=hi)
        is_like = False
        for like in video.likes.all():
            if like == request.user:
                is_like = True
                break
        if is_like:
            video.likes.remove(request.user)
        is_dislike = False
        for dislike in video.dislikes.all():
            if dislike == request.user:
                is_dislike = True
                break
        if not is_dislike:
            video.dislikes.add(request.user)
        if is_dislike:
            video.dislikes.remove(request.user)

        likes_count = video.likes.count()

        dislikes_count = video.dislikes.count()
        
        return JsonResponse({'likes_count': likes_count, 'liked': is_like, 'dislikes_count': dislikes_count, 'disliked': is_dislike})
    
    def test_func(self):
        return Profile.objects.all().filter(username=self.request.user).exists()

class Recommend(LoginRequiredMixin, UserPassesTestMixin, View):
    model = Video
    def get_redirect_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']

        video = Video.objects.get(id=hi)
        profile = Profile.objects.all().get(username=self.request.user)
        
        profile.recommendations_left -= 1
        video.recommendations += 1

        if (video.recommendations in MILESTONES) and video.recommendations > video.recommendation_milestones:
            video.recommendation_milestones = video.recommendations
            MilestoneNotification.objects.create(video=video, message=f'Your video "{video.title}" reached a recommendation milestone!')

        video.save()
        profile.save()

        recommend_count = video.recommendations
        
        return JsonResponse({'recommend_count': recommend_count, 'recommendations_left': profile.recommendations_left})
    
    def test_func(self):
        id = self.kwargs['id']
        video = Video.objects.get(id=id)
        if Profile.objects.all().filter(username=self.request.user).exists():
            if Profile.objects.all().get(username=self.request.user) != video.uploader:
                return Profile.objects.all().get(username=self.request.user).recommendations_left > 0
            return False
        return False

class DownloadVideo(View):
    def get(self, request, *args, **kwargs):
        e = self.kwargs['id']
        video = Video.objects.get(id=e)
        if video.uploader.id != 5:
            videothing = open(video.video_file.name, "rb")
            videocontent = videothing.read()
            videothing.close()

            response = HttpResponse(videocontent, content_type='video/mp4')
            response['Content-Disposition'] = 'attachment; filename="%s"' % f"{video.title}.mp4"

            return response
        else:
            html_content = "<html><body><h1>no</h1></body></html>"
            return HttpResponse(html_content, content_type='text/html')

class VideoSearch(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('query')
        video_list = Video.objects.filter(
            Q(title__icontains=query)
        ).exclude(unlisted=True).exclude(uploader__shadowbanned=True)

        context = {
            'video_list': video_list
        }


        return render(request, 'videos/search.html', context)
