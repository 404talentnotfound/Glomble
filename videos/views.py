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
from .forms import CommentForm
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views import View
from django.contrib.auth.models import User
from django.core.cache import cache
from datetime import datetime, timedelta
import tempfile
import magic
import os
import random
from Glomble.pc_prod import *
import subprocess

def getvideos(request):
    videos = list(Video.objects.all().exclude(unlisted=True).values())
    return JsonResponse({"videos": videos})

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
            if elapsed_time >= 0.3 * Video.objects.get(id=id).duration or elapsed_time >= 7.5:
                if not cache.get(f"{key}:viewed"):
                    video = Video.objects.get(id=id)
                    video.views.add(User.objects.all().get(id=request.user.id))
                    video.save()
                    cache.set(f"{key}:viewed", 1, timeout=None)
                    viewed = True
        else:
            viewed = True
    else:
        viewed = True

    view_count = Video.objects.get(id=id).views.count()
    return JsonResponse({"view_count": view_count, "viewed": viewed})

def update_video_like_count(request, id):
    like_count = Video.objects.get(id=id).likes.count()
    dislike_count = Video.objects.get(id=id).dislikes.count()
    return JsonResponse({"like_count": like_count, "dislike_count": dislike_count})

def update_comments_like_count(request, id):
    for comment in Comment.objects.filter(post=Video.objects.get(id=id)):
        like_count = comment.likes.count()
        dislike_count = comment.dislikes.count()
        print(like_count, dislike_count, comment.pk)
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
    paginate_by = 8

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryset = Video.objects.all()

        if sort_by == 'date-desc':
            queryset = queryset.order_by('-date_posted')
        elif sort_by == 'date-asc':
            queryset = queryset.order_by('date_posted')
        elif sort_by == 'likes-desc':
            queryset = queryset.annotate(num_likes=Count('likes')).order_by('-num_likes')
        elif sort_by == 'views-desc':
            queryset = queryset.annotate(num_views=Count('views')).order_by('-num_views')
        else:
            queryset = queryset.annotate(num_likes=Count('likes')).order_by('-num_likes')
        excluded_profiles = []
        if self.request.user.is_superuser:
            queryset = queryset.exclude(uploader__in=excluded_profiles)
        else:
            queryset = queryset.exclude(uploader__in=excluded_profiles).exclude(unlisted=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort-by')
        return context

class CreateVideo(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Video
    fields = ['title', 'notification_message', 'description', 'video_file', 'thumbnail', 'unlisted']
    template_name = 'videos/create_video.html'
    redirect_field_name = reverse_lazy('video-create')
    is_valid = None

    def test_func(self):
        return Profile.objects.all().filter(username=self.request.user).exists()

    def form_valid(self, form):
        cooldown_valid = True
        last_upload_time = cache.get(f"last_upload_{self.request.user.id}")

        if last_upload_time is not None and datetime.now() < last_upload_time + timedelta(minutes=2):
            form.add_error(None, "You can only upload one video every 2 minutes.")
            cooldown_valid = False
            return super().form_invalid(form)

        form.instance.uploader = Profile.objects.all().get(username=self.request.user)
        unique = False
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        out = ""

        if form.instance.unlisted:
            out += random.choice(chars)
        else:
            out += random.choice(chars)
        
        while not unique:
            for i in range(11):
                out += random.choice(chars)
            if not Video.objects.filter(id=out).exists():
                unique = True
            else:
                out = out[:1]

        form.instance.id = out

        if not 'thumbnail' in self.request.FILES:
            video_check = self.request.FILES['video_file']
            if cooldown_valid:
                if video_check.size < 75000000 and video_check.size > 1024:
                    try:
                        video_filename = os.path.join(BASE_DIR, f'media/uploads/video_files/{out}.mp4')
                        print(video_filename)
                        form.instance.video_file.name = f"{out}.mp4"
                        temp_video_file = tempfile.NamedTemporaryFile(delete=False)
                        temp_video_file.write(video_check.file.read())
                        vid = VideoFileClip(temp_video_file.name)
                        thumbnail_filename = os.path.join(BASE_DIR, f'media/uploads/thumbnails/{out}.png')
                        form.instance.thumbnail.name = f"media/uploads/thumbnails/{out}.png"
                        vid.save_frame(thumbnail_filename, t = 0)
                        if vid.duration <= 1200 and vid.duration > 1:
                            subprocess.run(f'''sudo ffmpeg -i {temp_video_file.name} -c:v libx264 -b:v 600k -c copy -preset ultrafast {video_filename}''', shell=True, check=True)
                            form.instance.duration = vid.duration
                            cache.set(f"last_upload_{self.request.user.id}", datetime.now(), timeout=None)
                            os.remove(temp_video_file.name)
                            self.is_valid = True
                            return super().form_valid(form)
                        else:
                            form.add_error(None, "This video is longer than 20 minutes or shorter than 1 second.")
                            return super().form_invalid(form)
                        
                    except Exception as e:
                        if self.is_valid != True:
                            form.add_error(None, f"An error occurred while processing your video, please try again later.")
                            return super().form_invalid(form)
                    finally:
                        try:
                            temp_video_file.close()
                        except:
                            pass
                else:
                    form.add_error(None, "An error occurred while uploading your video. Please make sure the video is under 50 megabytes and try again.")
                    return super().form_invalid(form)
        else:
            video_check = self.request.FILES['video_file']
            thumbnail_check = self.request.FILES['thumbnail']
            form.instance.thumbnail.name = f"{out}.png"
            temp_thumbnail_file = tempfile.NamedTemporaryFile(delete=False)
            for chunk in thumbnail_check.chunks():
                temp_thumbnail_file.write(chunk)
            mime = magic.Magic(mime=True).from_file(temp_thumbnail_file.name)
            if mime in ['image/jpeg', 'image/png']:
                if cooldown_valid:
                    if video_check.size < 75000000 and thumbnail_check.size < 10000000 and video_check.size > 1024 and thumbnail_check.size > 1024:
                        try:
                            video_filename = os.path.join(BASE_DIR, f'media/uploads/video_files/{out}.mp4')
                            form.instance.video_file.name = f"{out}.mp4"
                            temp_video_file = tempfile.NamedTemporaryFile(delete=False)
                            temp_video_file.write(video_check.file.read())
                            thumbnail_filename = os.path.join(BASE_DIR, f'media/uploads/thumbnails/{out}.png')
                            form.instance.thumbnail.name = f"{out}.png"
                            vid = VideoFileClip(temp_video_file.name)
                            if vid.duration <= 1200 and vid.duration > 1:
                                cache.set(f"last_upload_{self.request.user.id}", datetime.now(), timeout=None)
                                subprocess.run(f'''sudo ffmpeg -i {temp_video_file.name} -c:v libx264 -b:v 600k -c copy -preset ultrafast {video_filename}''', shell=True, check=True)
                                subprocess.run(f'sudo ffmpeg -y -i {temp_thumbnail_file.name} -vf scale=512:512 {thumbnail_filename}', shell=True, check=True)
                                form.instance.duration = vid.duration
                                cache.set(f"last_upload_{self.request.user.id}", datetime.now(), timeout=None)
                                self.is_valid = True
                                return super().form_valid(form)
                            else:
                                form.add_error(None, "This video is longer than 20 minutes or shorter than 1 second.")
                                return super().form_invalid(form)
                        except Exception as e:
                            if self.is_valid != True:
                                form.add_error(None, f"An error occurred while processing your video, please try again later.")
                                return super().form_invalid(form)
                        finally:
                            try:
                                os.remove(temp_video_file.name)
                                os.remove(temp_thumbnail_file.name)
                            except:
                                pass
                    else:
                        form.add_error(None, "An error occurred while uploading your video. Please make sure the video is under 50 megabytes and the thumbnail is under 10 megabytes.")
                        return super().form_invalid(form)
            else:
                form.add_error(None, "Invalid thumbnail, please try again with a valid thumbnail.")
                return super().form_invalid(form)

    def form_invalid(self, form):
        Video.objects.all().filter(id=self.object.id).delete()

        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

class DetailVideo(DetailView):
    def get(self, request, *args, **kwargs):
        e = self.kwargs['id']
        form = CommentForm()
        pen = Video.objects.get(id=e)
        desclen = None
        pre = None
        readmore = None
        if User.objects.filter(id=self.request.user.id).exists():
            user = User.objects.get(id=self.request.user.id)
            posts = Video.objects.all().annotate(num_likes=Count('likes')).order_by('-num_likes').exclude(views__in=[user]).exclude(unlisted=True).exclude(id=e)
        else:
            posts = None
        if pen.description is not None:
            has_desc = True
            desclen = len(pen.description)
            pre = pen.description[:25]
            readmore = pen.description[25:]
        else:
            has_desc = False

        comments = Comment.objects.filter(post=pen).annotate(num_likes=Count('likes')).order_by('-num_likes')
        comment_count = comments.count()
        context = {
            'e': e,
            'post': pen,
            'form': form,
            'comments': comments,
            'comment_amount': comment_count,
            'pre': pre,
            'readmore': readmore,
            'desclen': desclen,
            'has': has_desc,
            'recommended': posts,
        }

        return render(request, 'videos/detail_video.html', context)

    def post(self, request, *args, **kwargs):
        e = self.kwargs['id']
        pen = Video.objects.get(id=e)
        if pen.uploader.id != 5:
            hi = Video.objects.get(id=e).uploader
            form = CommentForm(request.POST)

            if form.is_valid():
                cooldown_key = f"user:{request.user.id}:cooldown"
                last_comment_time = cache.get(cooldown_key)
                if last_comment_time:
                    time_passed = datetime.now() - last_comment_time
                    if time_passed < timedelta(seconds=30):
                        return redirect(f'{reverse("video-detail", kwargs={"id": e})}')

                new_comment = form.save(commit=False)
                new_comment.commenter = Profile.objects.get(username=request.user)
                new_comment.post = pen
                new_comment.save()

                cache.set(cooldown_key, datetime.now(), timeout=30)

                return redirect(f'{reverse("video-detail", kwargs={"id": e})}')

            comments = Comment.objects.filter(post=pen).order_by('-date_posted')

            context = {
                'e': e,
                'post': pen,
                'form': form,
                'comments': comments,
            }
            return render(request, 'videos/detail_video.html', context)
        else:
            return redirect(f'{reverse("video-detail", kwargs={"id": e})}')

class UpdateVideo(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Video
    slug_url_kwarg = "id"
    slug_field = "id"
    fields = ['title', 'description', 'unlisted']
    template_name = 'videos/create_video.html'
        
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

class AddLike(LoginRequiredMixin, View):
    def get_redirect_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']
        video = Video.objects.get(id=hi)
        if video.uploader.id != 5:
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
        
        return JsonResponse({'likes_count': likes_count, 'liked': is_like, 'dislikes_count': dislikes_count, 'disliked': is_dislike})
        
class Dislike(LoginRequiredMixin, View):
    def get_redirect_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']
        video = Video.objects.get(id=hi)
        if video.uploader.id != 5:
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
        excluded_uploaders = [5]
        video_list = Video.objects.filter(
            Q(title__icontains=query)
        ).exclude(uploader__in=excluded_uploaders).exclude(unlisted=True)

        context = {
            'video_list': video_list
        }


        return render(request, 'videos/search.html', context)
