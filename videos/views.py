from django.shortcuts import render, reverse, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from .models import Video, Comment, batch_calculate_score
from django.db.models import Q, Count
from itertools import chain
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from profiles.models import Profile
from .forms import CommentForm, ReplyForm, AdminDeleteObjectForm
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.contrib.auth.models import User
from django.core.cache import cache
from notifications.models import MilestoneNotification, MiscellaneousNotification, send_misc_notification
from Glomble.pc_prod import *
from datetime import datetime, timedelta
from PIL import Image
import tempfile
import os
import random
import subprocess
from .templatetags.count import get_media_url
from .cron import remove_inactive_users
from django.core.files import File

def glimble(request):
    return render(request, "glimble.html")

def get_recommended_videos(request, category):
    try:
        videos = Video.objects.all().filter(category=category).exclude(unlisted=True).exclude(uploader__shadowbanned=True).exclude(uploader__banned=True).order_by("?")[:3]
    except:
        videos = []
    rendered_html = render(request, 'videos/video_cards.html', {'object_list': videos})
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

def handler500(request, exception, template_name="500.html"):
    response = render(template_name)
    response.status_code = 500
    return response

def related_links(request):
    return render(request, "videos/related_links.html")

def redirect_index(request):
    return redirect('/')

def redirect_video(request, id):
    return redirect(f'{reverse("video-detail", kwargs={"id": id})}')

def mcdonalds(request):
    return redirect('https://mcdonalds.com')

def tos_page(request):
    return redirect('https://docs.google.com/document/d/1yLgjILLIyZ_wheT9Nf3y9j3u3kcGJua6phvBKHIcfJU')

class Index(ListView):
    model = Video
    template_name = 'videos/index.html'
    context_object_name = 'videos'
    paginate_by = 54

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        category = self.request.GET.get('category')
        by = self.request.GET.get('by')
        query = self.request.GET.get('query')

        remove_inactive_users()

        queryset = Video.objects.all().exclude(unlisted=True).exclude(uploader__shadowbanned=True).exclude(uploader__banned=True)

        profile = None

        if self.request.user.is_authenticated:
            profile = Profile.objects.all().get(username=self.request.user)

        if query:
            queryset = queryset.filter(Q(title__icontains=query))

        if category and category != "all":
            queryset = queryset.filter(category=category.capitalize())

        if by and by != "all" and profile:
            if by == "followers":
                queryset = queryset.filter(uploader__username__in=profile.followers.all())
            elif by == "following":
                queryset = queryset.filter(uploader__in=profile.following.all())
            elif by == "mutual":
                queryset = queryset.filter(uploader__username__in=profile.followers.all()).filter(uploader__in=profile.following.all())

        if sort_by == 'newest':
            queryset = queryset.order_by('-date_posted')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('date_posted')
        elif sort_by == 'likes':
            queryset = queryset.annotate(num_likes=Count('likes')).order_by('-num_likes')
        elif sort_by == 'views':
            queryset = queryset.annotate(num_views=Count('views')).order_by('-num_views')
        elif sort_by == "recommended":
            queryset = queryset.annotate(num_likes=Count('likes')).order_by("-score", '-num_likes')
        elif sort_by == "random":
            queryset = queryset.order_by("?")
        elif sort_by == 'NUMNOM' and self.request.user.id == 1:
            queryset = queryset.annotate(num_nom=Count('nominations')).order_by('-num_nom').exclude(num_nom=0)
        else:
            queryset = queryset.annotate(num_likes=Count('likes')).order_by("-score", '-num_likes')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = ""
        sort_by = self.request.GET.get('sort-by')
        if sort_by:
            params += f"&sort-by={sort_by}"

        category = self.request.GET.get('category')
        if category:
            params += f"&category={category}"

        query = self.request.GET.get('query')
        if query:
            params += f"&query={query}"

        by = self.request.GET.get('by')
        if by:
            params += f"&by={by}"
        
        context['sort_by'] = sort_by
        context['category'] = category
        context['query'] = query
        context['by'] = by
        context['params'] = params
        return context

class CreateVideo(LoginRequiredMixin, CreateView):
    model = Video
    fields = ['title', 'notification_message', 'description', 'category', 'video_file', 'thumbnail', 'unlisted', 'push_notification']
    template_name = 'videos/create_video.html'
    redirect_field_name = reverse_lazy('video-create')
    is_valid = None

    # not really necessary but it just looks so clunky doing it manually every time
    def upload_error(self, form, msg):
        form.add_error(None, msg)
        return self.form_invalid(form)
    
    def get_video_length(self, filename):
        result = subprocess.run(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {filename}",
            shell=True,
            check=True,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
        )

        try:
            return float(result.stdout)
        except:
            return None

    def form_valid(self, form):
        last_upload_time = cache.get(f"last_upload_{self.request.user.id}")

        if last_upload_time and datetime.now() < last_upload_time + timedelta(minutes=2):
            self.upload_error(form, "You can only upload one video every 2 minutes.")

        form.instance.uploader = Profile.objects.get(username=self.request.user)

        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        video_id = ""
        
        while True:
            for _ in range(12):
                video_id += random.choice(chars)  # wonderful code
            if not Video.objects.filter(id=video_id).exists():
                break
            else:
                video_id = ""

        form.instance.id = video_id

        uploaded_video = self.request.FILES['video_file']
        if not 1024 < uploaded_video.size < 100000000:
            self.upload_error(form, "The video size must be between 1kb and 100mb.")
        
        temp_video_file = tempfile.NamedTemporaryFile(delete=False)
        temp_video_file.write(uploaded_video.read())
        
        try:
            uploaded_thumbnail = self.request.FILES['thumbnail']
            if not 1024 < uploaded_thumbnail.size < 5000000:
                self.upload_error(form, "The thumbnail size must be between 1kb and 5mb.")
            temp_thumbnail_file = tempfile.NamedTemporaryFile(delete=False)
            temp_thumbnail_file.write(uploaded_thumbnail.read())
        except:
            uploaded_thumbnail = False

        try:
            duration = self.get_video_length(temp_video_file.name)
            if duration != None and (duration > 7200 or duration < 1):
                self.upload_error(form, "The video duration must be between 1 second and 2 hours.")

            video_filename = os.path.join(BASE_DIR, f"{video_id}.mp4")

            subprocess.run(
                f"""ffmpeg -i {temp_video_file.name} -vf "scale='min(1920,iw)':-1" -c:v libx264 -pix_fmt yuv420p -crf 27 -preset faster {video_filename}""",
                shell=True,
                check=True,
            )

            temp_video_file.close()
            
            # this is a bit redundant but I want to prevent videos with doctored lengths from being uploaded
            # while also not having to reencode them if they're unaltered
            # there is probably a better way though
            duration = self.get_video_length(video_filename)
            if duration == None or duration > 7200 or duration < 1:
                self.upload_error(form, "The video duration must be between 1 second and 2 hours.")

            with open(video_filename, "rb") as f:
                form.instance.video_file.save(
                    f"uploads/video_files/{video_id}.mp4",
                    File(f),
                    save=False
                )

            try:
                gif = False
                if uploaded_thumbnail.name[-3:] != "gif":
                    thumbnail_filename = os.path.join(BASE_DIR, f"{video_id}.jpg")
                else:
                    gif = True
                    thumbnail_filename = os.path.join(BASE_DIR, f"{video_id}.gif")
            except:
                gif = False
                thumbnail_filename = os.path.join(BASE_DIR, f"{video_id}.jpg")
            
            if uploaded_thumbnail:
                ttsize = Image.open(temp_thumbnail_file.name).size
                ttwidth, ttheight = ttsize
                ffarg = '-vf scale=720:-1' if ttwidth > ttheight else '-vf scale=-1:720'
                
                subprocess.run(
                    f"ffmpeg -i {temp_thumbnail_file.name} {ffarg if max(ttsize) > 720 else ''} {thumbnail_filename}",
                    shell=True,
                    check=True,
                )
                
                if gif:
                    form.instance.thumbnail.name = f"uploads/thumbnails/{video_id}.gif"
                else:
                    form.instance.thumbnail.name = f"uploads/thumbnails/{video_id}.jpg"
            
            else:
                result = subprocess.run(
                    f"ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0:s=x {video_filename}",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    check=True,
                )
                ttsize = tuple(map(int, result.stdout.decode("utf-8").split("x")))
                ttwidth, ttheight = ttsize
                ffarg = '-vf scale=720:-1' if ttwidth > ttheight else '-vf scale=-1:720'
                form.instance.thumbnail.name = f"uploads/thumbnails/{video_id}.jpg"
                subprocess.run(
                    f"ffmpeg -i {video_filename} -frames:v 1 {ffarg if max(ttsize) > 720 else ''} {thumbnail_filename}",
                    shell=True,
                    check=True,
                )

            with open(thumbnail_filename, "rb") as f:
                form.instance.thumbnail.save(
                    f"uploads/thumbnails/{video_id}.{'gif' if gif else 'jpg'}",
                    File(f),
                    save=False
                )

            form.instance.video_file.name = f"uploads/video_files/{video_id}.mp4"

            form.instance.duration = duration

            cache.set(f"last_upload_{self.request.user.id}", datetime.now(), timeout=None)

            return super().form_valid(form)

        except Exception as e:
            form.add_error(None, f"An error occurred during processing.")
            return self.form_invalid(form)

        finally:
            if video_filename != None and os.path.exists(video_filename):
                os.remove(video_filename)
            if temp_video_file != None and os.path.exists(temp_video_file.name):
                os.remove(temp_video_file.name)
            if thumbnail_filename != None and os.path.exists(thumbnail_filename):
                os.remove(thumbnail_filename)

    def form_invalid(self, form):
        if hasattr(self, 'object') and self.object:
            try:
                client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=self.object.video_file.name)
                client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=self.object.thumbnail.name)
            except:
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
        can_nominate = pen.date_posted.year==timezone.now().year
        if pen.description != "":
            has_desc = True
            desclen = len(pen.description)
            pre = pen.description[:250]
            readmore = pen.description[250:]
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

        viewable_comments = pen.comments.all().exclude(commenter__shadowbanned=True).exclude(commenter__banned=True)

        replies = viewable_comments.exclude(replying_to=None).order_by('date_posted')

        comments = viewable_comments.filter(replying_to=None).annotate(num_likes=Count('likes')).order_by('-num_likes')
        comment_count = viewable_comments.count()

        context = {
            'e': e,
            'post': pen,
            'profile': pen.uploader,
            'form': form,
            'replyform': replyform,
            'comments': comments,
            'comment_amount': comment_count,
            'pre': pre,
            'readmore': readmore,
            'desclen': desclen,
            'has': has_desc,
            'is_following': is_following,
            'replies': replies,
            'can_nominate': can_nominate,
        }

        if pen.pinned_comment != None:
            pinned_comment = Comment.objects.all().filter(pk=pen.pinned_comment.pk)
            comments = chain(pinned_comment, comments.exclude(pk=pen.pinned_comment.pk))

            context.update({'comments':comments, 'pinned_comment':pinned_comment.first()})

        return render(request, 'videos/detail_video.html', context)

    def post(self, request, *args, **kwargs):
        e = self.kwargs['id']
        if not request.user.is_authenticated:
            return reverse('video-detail', kwargs={'id': e})
        
        pen = Video.objects.get(id=e)
        form = CommentForm(request.POST)
        replyform = ReplyForm(request.POST)

        desclen = None
        pre = None
        readmore = None

        viewable_comments = pen.comments.all().exclude(commenter__shadowbanned=True).exclude(commenter__banned=True)

        if pen.description is not None:
            has_desc = True
            desclen = len(pen.description)
            pre = pen.description[:250]
            readmore = pen.description[250:]
        else:
            has_desc = False

        profile = Profile.objects.all().get(username=request.user)

        is_following = pen.uploader in profile.following.all()

        comments = viewable_comments.filter(replying_to=None).annotate(num_likes=Count('likes')).order_by('-num_likes')
        comment_count = viewable_comments.count()

        pinned_comment = pen.pinned_comment
        
        if pinned_comment != None:
            comments = [pinned_comment, comments]

        replies = viewable_comments.exclude(replying_to=None).order_by('date_posted')

        context = {
            'e': e,
            'post': pen,
            'form': CommentForm(),
            'replyform': ReplyForm(),
            'comments': comments,
            'pinned_comment': pinned_comment,
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

        if last_comment_time and datetime.now() < last_comment_time + timedelta(seconds=30):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                rendered_comments = render(request, 'videos/comment.html', context)
                return JsonResponse({
                    "success": False,
                    "comments": rendered_comments.content.decode('utf-8'),
                    "count": viewable_comments.count(),
                })
            return render(request, 'videos/detail_video.html', context)
        
        if not form.is_valid() or not replyform.is_valid():
            return render(request, 'videos/detail_video.html', context)

        if form_type == "comment":
            new_comment = form.save(commit=False)
            new_comment.commenter = profile
            new_comment.post = pen
            new_comment.save()

            pen.comments.add(new_comment)

            cache.set(f"last_comment_{self.request.user.id}", datetime.now(), timeout=None)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                all_replies = viewable_comments.filter(replying_to=None)
                queryset = all_replies.filter(pk=new_comment.pk) | all_replies.exclude(pk=new_comment.pk)

                if pinned_comment != None:
                    queryset = all_replies.filter(pk=pinned_comment.pk) | queryset

                context.update({'comments': queryset})
                rendered_comments = render(request, 'videos/comment.html', context)

                return JsonResponse({
                    "success": True,
                    "comments": rendered_comments.content.decode('utf-8'),
                    "count": viewable_comments.count(),
                })

            return redirect(f'{reverse("video-detail", kwargs={"id": e})}')

        elif form_type == "reply":
            new_reply = replyform.save(commit=False)
            new_reply.replying_to = Comment.objects.get(id=int(request.POST.get("comment_id")))

            if new_reply.replying_to.post != pen:
                return JsonResponse({
                    "success": False,
                    "comments": rendered_comments.content.decode('utf-8'),
                    "count": viewable_comments.count(),
                })

            new_reply.commenter = profile
            new_reply.post = pen
            new_reply.save()

            pen.comments.add(new_reply)
            new_reply.replying_to.replies.add(new_reply)

            cache.set(f"last_comment_{self.request.user.id}", datetime.now(), timeout=None)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                all_replies = pen.comments.all().exclude(commenter__shadowbanned=True).exclude(commenter__banned=True).exclude(replying_to=None)
                context.update({'replies': all_replies})
                rendered_comments = render(request, 'videos/comment.html', context)

                return JsonResponse({
                    "success": True,
                    "comments": rendered_comments.content.decode('utf-8'),
                    "count": viewable_comments.count(),
                })
            
            return redirect(f'{reverse("video-detail", kwargs={"id": e})}')

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
        video = self.get_object()
        form = AdminDeleteObjectForm(request.POST)

        if not request.user.is_superuser or request.user == video.uploader.username:
            return super().delete(request, *args, **kwargs)
        
        if form.is_valid() and form.cleaned_data["notify"]:
            send_misc_notification([video.uploader], message=f"Your comment was deleted \"{form.cleaned_data['notification_message']}\"")
        
        return super().delete(request, *args, **kwargs)
        
    def get(self, request, *args, **kwargs):
        form = AdminDeleteObjectForm()

        context = {
            "form": form,
        }

        return render(request, 'videos/delete_video.html', context)
        

class AddLike(LoginRequiredMixin, View):
    def get_redirect_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']
        video = Video.objects.get(id=hi)
        is_dislike = False
        if request.user in video.dislikes.all():
            is_dislike = True
            video.dislikes.remove(request.user)

        is_like = False
        if request.user in video.likes.all():
            is_like = True

        if not is_like:
            video.likes.add(request.user)

        if is_like:
            video.likes.remove(request.user)

        likes_count = video.likes.count()

        dislikes_count = video.dislikes.count()
        
        return JsonResponse({'likes_count': likes_count, 'liked': not is_like, 'dislikes_count': dislikes_count, 'disliked': is_dislike})
        
class Dislike(LoginRequiredMixin, View):
    def get_redirect_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']
        video = Video.objects.get(id=hi)
        is_like = False
        if request.user in video.likes.all():
            is_like = True
            video.likes.remove(request.user)

        is_dislike = False

        if request.user in video.dislikes.all():
            is_dislike = True

        if not is_dislike:
            video.dislikes.add(request.user)
        if is_dislike:
            video.dislikes.remove(request.user)

        likes_count = video.likes.count()

        dislikes_count = video.dislikes.count()
        
        return JsonResponse({'likes_count': likes_count, 'liked': is_like, 'dislikes_count': dislikes_count, 'disliked': is_dislike})

class Recommend(LoginRequiredMixin, UserPassesTestMixin, View):
    model = Video
    def get_redirect_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']

        video = Video.objects.get(id=hi)
        profile = Profile.objects.all().get(username=self.request.user)

        has_recommended = True

        if profile in video.recommendations.all():
            has_recommended = False
            video.recommendations.remove(profile)
        else:
            video.recommendations.add(profile)

        if (video.recommendations.count() in MILESTONES) and video.recommendations.count() > video.recommendation_milestones:
            video.recommendation_milestones = video.recommendations.count()
            MilestoneNotification.objects.create(video=video, message=f'Your video "{video.title}" reached a recommendation milestone of {video.recommendations.count()} people!')

        video.save()

        score = video.score

        return JsonResponse({'score': score, 'has_recommended': has_recommended})
    
    def test_func(self):
        id = self.kwargs['id']
        video = Video.objects.get(id=id)
        return Profile.objects.all().get(username=self.request.user) != video.uploader
    
# This is for glomble rewind and should only be available during december (i really hope i finish this update before that)
# Hi i'm writing this on Nov 28, the odds of finishing every feature i have planned is not too looking good
# Note from Nov 30: uh oh
class Nominate(LoginRequiredMixin, UserPassesTestMixin, View):
    model = Video
    def get_redirect_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']

        video = Video.objects.get(id=hi)
        profile = Profile.objects.all().get(username=self.request.user)

        has_nominated = True

        if profile.nominated_video == video:
            profile.nominated_video = None
            video.nominations.remove(profile)
            has_nominated = False
        else:
            if profile.nominated_video:
                profile.nominated_video.nominations.remove(profile)
            video.nominations.add(profile)
            profile.nominated_video = video

        profile.save()

        return JsonResponse({'has_nominated': has_nominated, 'is_video': True})
    
    def test_func(self):
        id = self.kwargs['id']
        video = Video.objects.get(id=id)
        return Profile.objects.all().get(username=self.request.user) != video.uploader and video.date_posted.year == timezone.now().year and timezone.now().month == 12

class DownloadVideo(View):
    def get(self, request, *args, **kwargs):
        e = self.kwargs['id']
        video = Video.objects.get(id=e)
        if video.uploader.id != "5HKiuWuT12Bs":
            return redirect(f'{get_media_url()}/{video.video_file.name}')
        html_content = "<html><body><h1 style='text-align: center;'>no</h1></body></html>"
        return HttpResponse(html_content, content_type='text/html')
