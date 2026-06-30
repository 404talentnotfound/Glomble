from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from .models import Profile, Chat, Message, ProfileCustomisation, ProfileRating, BanAppeal, Ban
from videos.models import Video, Comment
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.contrib.auth.models import User
from django.views import View
from django.db.models import Q, Count, Max
from .forms import UserRegisterForm, MessageForm, ProfileCustomisationForm, ProfileRatingForm, BanAppealForm, ResendEmailForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .decorators import user_not_authenticated
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from .tokens import account_activation_token
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from datetime import datetime, timedelta
from Glomble.pc_prod import *
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from notifications.models import MilestoneNotification
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import EmailMessage
from videos.templatetags.count import can_appeal
import os
import random
import tempfile
import subprocess
from reports.models import BugReport, Suggestion
from operator import attrgetter

@login_required
def rate_profile(request, id):
    profile = get_object_or_404(Profile, id=id)

    if request.method == "POST":
        form = ProfileRatingForm(request.POST)
        if form.is_valid():
            rating_value = form.cleaned_data['rating']
            obj, created = ProfileRating.objects.update_or_create(
                rater=request.user,
                rated_profile=profile,
                defaults={'rating': rating_value}
            )
            profile.recalculate_rating()
            return JsonResponse({"success": True, "new_rating": profile.rating}, status=200)
        return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        try:
            current_rating = ProfileRating.objects.get(rater=request.user, rated_profile=profile).rating
        except ProfileRating.DoesNotExist:
            current_rating = 0
        form = ProfileRatingForm(initial={"rating": current_rating})
        return JsonResponse({"form": form.as_p()})

@login_required
def customise_profile(request, id):
    customised_profile = get_object_or_404(Profile, id=id)
    if request.user != customised_profile.username:
        return redirect('detail-profile', id=id)

    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    random_id = "".join(random.choice(chars) for _ in range(5))

    customisation, created = ProfileCustomisation.objects.get_or_create(customised_profile=customised_profile)
    if request.method == "POST":
        form = ProfileCustomisationForm(request.POST, request.FILES, instance=customisation)
        if form.is_valid():
            if 'banner_image' in request.FILES:
                client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=customised_profile.customisation.banner_image.name)

                banner = request.FILES['banner_image']
                form.save(commit=False)
                temp_banner = tempfile.NamedTemporaryFile(delete=False)
                for chunk in banner.chunks():
                    temp_banner.write(chunk)
                form.instance.banner_image = f"profiles/banners/{customised_profile.id}-{random_id}.jpg"

                try:
                    subprocess.run(f"ffmpeg -y -i {temp_banner.name} {customised_profile.id}-banner.jpg", shell=True, check=True)
                except:
                    form.add_error("banner_image","An error occurred processing this file, please try another.")
                    return render(request, 'profiles/customise_profile.html', {'form': form, 'customised_profile': customised_profile})

                with open(f'{customised_profile.id}-banner.jpg') as pfp_file:
                    client.upload_fileobj(
                        pfp_file.buffer,
                        AWS_STORAGE_BUCKET_NAME,
                        f"profiles/banners/{customised_profile.id}-{random_id}.jpg",
                        ExtraArgs={"ContentType": 'image/jpg'},
                    )

                temp_banner.close()

                os.remove(f"{customised_profile.id}-banner.jpg")
                os.remove(temp_banner.name)
                    
            if 'video_banner' in request.FILES:
                client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=customised_profile.customisation.video_banner.name)

                banner = request.FILES['video_banner']
                form.save(commit=False)
                temp_video_banner = tempfile.NamedTemporaryFile(delete=False)
                for chunk in banner.chunks():
                    temp_video_banner.write(chunk)
                form.instance.video_banner = f"profiles/video_banners/{customised_profile.id}-{random_id}.jpg"

                try:
                    subprocess.run(f"ffmpeg -y -i {temp_video_banner.name} -vf scale=256:220 {customised_profile.id}-videobanner.jpg", shell=True, check=True)
                except:
                    form.add_error("video_banner","An error occurred processing this file, please try another.")
                    return render(request, 'profiles/customise_profile.html', {'form': form, 'customised_profile': customised_profile})

                with open(f'{customised_profile.id}-videobanner.jpg') as pfp_file:
                    client.upload_fileobj(
                        pfp_file.buffer,
                        AWS_STORAGE_BUCKET_NAME,
                        f"profiles/video_banners/{customised_profile.id}-{random_id}.jpg",
                        ExtraArgs={"ContentType": 'image/jpg'},
                    )

                temp_video_banner.close()

                os.remove(f"{customised_profile.id}-videobanner.jpg")
                os.remove(temp_video_banner.name)
                
            form.save()

            customised_profile.customisation = form.instance
            customised_profile.save()

            return redirect('detail-profile', id=id)
    else:
        form = ProfileCustomisationForm(instance=customisation)
    
    return render(request, 'profiles/customise_profile.html', {'form': form, 'customised_profile': customised_profile})

# creates a profile for a user if they don't yet have one
# returns profile ID if created, otherwise returns false
def create_profile(user):
    if Profile.objects.filter(username=user).exists():
        return False
    
    profile = Profile(username=user)
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    out = ""
    
    while True:
        for _ in range(12):
            out += random.choice(chars)
        if not Profile.objects.filter(id=out).exists():
            break
        else:
            out = ""

    profile.id = out
    profile.profile_picture.name = "profiles/pfps/default.png"
    profile.save()

    return out

# Temporary function, very inefficent but it only has to run once so it's fine
def migrate_changes():
    profiles = Profile.objects.all()

    for i, profile in enumerate(profiles):
        followed_creators = profiles.filter(followers__in=[profile.username])
        profile.following.set(followed_creators)
        profile.comments.set(Comment.objects.all().filter(commenter=profile))

def update_profile_follow_count(request, id):
    follow_count = Profile.objects.get(id=id).followers.count()
    return JsonResponse({"follow_count": follow_count})

@user_not_authenticated
def resend_activation_page(request):
    if request.method == "POST":
        form = ResendEmailForm(request.POST)
        
        if form.is_valid():
            data = form.cleaned_data
            if data['username']:
                user = User.objects.all().filter(username=data['username'])
            elif data['email']:
                user = User.objects.all().filter(email=data['email'])

            should_send = True

            if not user.exists():
                form.add_error(None, "A user matching this email or username does not exist")
                return render(request, "profiles/resend_email.html", {'form': form})

            user = user.get()

            last_email_time = cache.get(f"last_email_{user.id}")
            if last_email_time and datetime.now() < last_email_time + timedelta(minutes=2):
                form.add_error(None, "Email was not sent (2 minute cooldown)")
                should_send = False

            if user.is_active:
                form.add_error(None, "The matching user's email has already been verified")
                should_send = False
            
            if should_send:
                activateEmail(request, user, user.email)
                cache.set(f"last_email_{user.id}", datetime.now(), timeout=None)
                messages.success(request, "Email sent! If you cannot find it try checking in your spam folder (it does actually end up there sometimes!)")
                return render(request, "profiles/resend_email.html", {'form': form})
    else:
        form = ResendEmailForm()
    return render(request, "profiles/resend_email.html", {'form': form})
    
def redirect_profile(request, id):
    return redirect(f"{reverse('detail-profile', kwargs={'id': id})}")

class ProfileIndex(ListView):
    model = Profile
    template_name = "profiles/index.html"
    paginate_by = 20

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryfilter = self.request.GET.get('filter')
        query = self.request.GET.get('query')
        queryset = Profile.objects.all()

        request_profile = None

        if not self.request.user.is_anonymous and Profile.objects.all().filter(username=self.request.user).exists():
            request_profile = Profile.objects.all().get(username=self.request.user)

        hidden = False

        if queryfilter and request_profile:
            if queryfilter == "mutual":
                queryset = request_profile.following.filter(username__in=request_profile.followers.all())
            elif queryfilter == "following":
                queryset = request_profile.following
            elif queryfilter == "followers":
                queryset = queryset.filter(username__in=request_profile.followers.all())
            elif queryfilter == "hidden" and self.request.user.is_superuser:
                queryset = queryset.filter(shadowbanned=True) | queryset.filter(banned=True)
                hidden = True

        if query:
            queryset = queryset.filter(username__username__icontains=query)

        queryset = queryset.annotate(num_followers=Count('followers'))

        if sort_by == 'date-desc':
            queryset = queryset.order_by('-date_made')
        elif sort_by == 'date-asc':
            queryset = queryset.order_by('date_made')
        elif sort_by == 'followers-desc':
            queryset = queryset.order_by('-num_followers')
        elif sort_by == 'ratings':
            queryset = queryset.order_by('-rating', '-num_followers')
        elif sort_by == 'NUMBNOMB' and self.request.user.id == 1:
            queryset = queryset.annotate(num_nom=Count('noms')).order_by('-num_nom').exclude(num_nom=0)
        else:
            queryset = queryset.order_by('-num_followers')
        
        if not hidden:
            queryset = queryset.exclude(shadowbanned=True).exclude(banned=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = ""
        sort_by = self.request.GET.get('sort-by')
        if sort_by:
            params += f"&sort-by={sort_by}"

        filter = self.request.GET.get('filter')
        if filter:
            params += f"&filter={filter}"

        query = self.request.GET.get('query')
        if query:
            params += f"&query={query}"

        context['sort_by'] = sort_by
        context['filter'] = filter
        context['query'] = query
        context['params'] = params
        return context

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, "Thank you for your email confirmation. Now you can log into your account.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid!")
        return redirect('login') 

@user_not_authenticated
def register(req):
    if req.method == "POST":
        Form = UserRegisterForm(req.POST)
        if Form.is_valid():
            user = Form.save(commit=False)
            user.is_active=False
            user.save()
            username = Form.cleaned_data.get("username")
            email = Form.cleaned_data.get("email")
            activateEmail(req, user, email)
            messages.success(req, f"Hello {user}, please go to your email {email} inbox and click on \
                the activation link to confirm and complete the registration. Note: If you can't find the email, check your spam folder.")
            create_profile(user)
            return redirect("login")
    else:
        Form = UserRegisterForm()
    return render(req, "profiles/register.html", {'form': Form})

class CustomPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        email = form.cleaned_data['email']
        mail_subject = "Reset your Glomble password"
        user = Profile.objects.all().get(username=User.objects.all().get(email=email))
        uid = urlsafe_base64_encode(force_bytes(user.username.id))
        token = default_token_generator.make_token(user.username)
        reset_url = self.request.build_absolute_uri(
            reverse('password_reset_confirm', args=[uid, token])
        )
        html_thing = render_to_string('profiles/password_reset_email.html', {"reset_url": reset_url, "user": user.username.username})
        email_to_send = EmailMessage(mail_subject, html_thing, to=[email])
        email_to_send.content_subtype = "html"
        email_to_send.send()
        return redirect('password_reset_done')

def activateEmail(request, user, to_email):
    mail_subject = "Activate your Glomble user account"
    message = render_to_string("template_activate_account.html", {
        'user': user,
        'domain': "glomble.com",
        'uid': urlsafe_base64_encode(force_bytes(user.id)),
        'token': account_activation_token.make_token(user),
        "protocol": 'https' if request.is_secure() else 'http'
    })
    email_to_send = EmailMessage(mail_subject, message, to=[to_email])
    email_to_send.content_subtype = "html"
    email_to_send.send()

# dear lord this shit sucks ass I really need to rewrite this
# note from the future: I did technically rewrite it in the sense that I replaced it with this comment line (not only was it bad but it was also completely unnecessary)

class DetailProfileIndex(ListView):
    model = Profile
    slug_url_kwarg = "id"
    slug_field = "id"
    template_name = 'profiles/detail_profile.html'
    def get(self, request, *args, **kwargs):
        identity = self.kwargs['id'] # why the hell did i name the variable "identity" lmao

        if Profile.objects.filter(id=identity).exists():
            profile = Profile.objects.get(id=identity)
        elif Profile.objects.filter(username__username=identity).exists():
            profile_id = Profile.objects.get(username__username=identity).id
            return redirect(reverse("detail-profile", kwargs={"id": profile_id}))
        else:
            return
        
        if profile.banned:
            return render(request, "profiles/banned_profile.html")

        info = profile.bio
        pfp = profile.profile_picture
        username = profile.username
        if (request.user.is_superuser or profile.moderator) or username == request.user:
            posts = profile.videos.all().order_by("-date_posted")
        else:
            posts = profile.videos.all().exclude(unlisted=True).order_by("-date_posted")
        followers = profile.followers.all()
        follow_num = followers.count()
        following_num = profile.following.count()

        is_following = request.user in followers

        context = {
            'info': info,
            'id': profile.id,
            'pfp': pfp,
            'username': username,
            'object_list': posts,
            'follow_num': follow_num,
            'following_num': following_num,
            'is_following': is_following,
            'profile': profile,
        }
        return render(request, 'profiles/detail_profile.html', context)
    
# I love it when code I wrote ages ago has 9 layers of indentation 🥰
class UpdateProfile(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Profile
    slug_url_kwarg = "id"
    slug_field = "id"
    fields = ['profile_picture','bio']
    template_name = "profiles/update_profile.html"
    def form_valid(self, form):
        profile = Profile.objects.get(id=self.kwargs['id'])
        last_upload_time = cache.get(f"last_profileupdate_{self.request.user.id}")

        if last_upload_time is not None and datetime.now() < last_upload_time + timedelta(minutes=1):
            form.add_error(None, "You can only update your profile every minute.")
            return super().form_invalid(form)

        if form.is_valid():
            try:
                if 'profile_picture' in self.request.FILES:
                    newpfp = self.request.FILES['profile_picture']
                    temp_pfp = tempfile.NamedTemporaryFile(delete=False)
                    for chunk in newpfp.chunks():
                        temp_pfp.write(chunk)
                    try:
                        if profile.profile_picture.name != "profiles/pfps/default.png":
                            try:
                                client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=profile.profile_picture.name)
                            except Exception as e:
                                pass
                    except Exception as e:
                        pass

                    cache.set(f"last_profileupdate_{self.request.user.id}", datetime.now(), timeout=None)

                    subprocess.run(f"ffmpeg -y -i {temp_pfp.name} -vf scale=512:512 {profile.id}.jpg", shell=True, check=True)

                    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
                    random_id = "".join(random.choice(chars) for _ in range(5))

                    form.instance.profile_picture = f"profiles/pfps/{profile.id}-{random_id}.jpg"

                    with open(f'{profile.id}.jpg') as pfp_file:
                        client.upload_fileobj(
                            pfp_file.buffer,
                            AWS_STORAGE_BUCKET_NAME,
                            f"profiles/pfps/{profile.id}-{random_id}.jpg",
                            ExtraArgs={"ContentType": 'image/jpg'},
                        )

                    temp_pfp.close()

                    os.remove(f"{profile.id}.jpg")
                    os.remove(temp_pfp.name)

                    return super().form_valid(form)
                else:
                    if form.instance.profile_picture == "" or profile.profile_picture.name == "":
                        form.instance.profile_picture = f"profiles/pfps/default.png"

                    return super().form_valid(form)

            except Exception as e:
                form.add_error(None, f"An error occurred while updating your profile.")
                return super().form_invalid(form)
        else:
            form.add_error(None, "An error occurred while updating your profile. Please make sure the profile you are logged into is the profile you want to update.")
            return super().form_invalid(form)

    def get_success_url(self):
        return reverse('detail-profile', kwargs={'id': self.object.id})

    def test_func(self):
        profile = self.get_object()
        return self.request.user == profile.username or ((self.request.user.is_superuser or profile.moderator) and profile.id != CREATOR_ID)

class DeleteProfile(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Profile
    template_name = 'profiles/delete_profile.html'
    slug_url_kwarg = "id"
    slug_field = "id"
    def get_redirect_url(self):
        return reverse('detail-profile', kwargs={'id': self.object.id})

    def get_success_url(self):
        profile = self.get_object()
        profile.delete_media()

        Chat.objects.all().filter(members__in=[profile]).delete()
        profile.username.delete()
        return reverse('index')
        
    def test_func(self):
        profile = self.get_object()
        return self.request.user == profile.username or self.request.user.is_superuser

class AddFollower(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_redirect_url(self):
        return reverse('detail-profile', kwargs={'id': self.object.id})
    
    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']
        profilething = Profile.objects.get(id=hi)
        currentprofile = Profile.objects.get(username=self.request.user)

        profilething.followers.add(request.user)
        currentprofile.following.add(profilething)

        followers_count = profilething.followers.count()

        if (followers_count in MILESTONES) and followers_count > profilething.follower_milestones:
            profilething.follower_milestones = followers_count
            profilething.save()
            MilestoneNotification.objects.create(profile=profilething, message=f"Your profile reached a follower milestone of {followers_count} people!")

        return JsonResponse({'follow_count': followers_count})
    
    def test_func(self):
        hi = self.kwargs['id']
        profilething = Profile.objects.get(id=hi)
        currentprofile = Profile.objects.filter(username=self.request.user)
        return currentprofile.exists() and currentprofile.first() != profilething
    
class Nominate(LoginRequiredMixin, UserPassesTestMixin, View):
    model = Profile
    def get_redirect_url(self):
        return reverse('video-detail', kwargs={'id': self.object.id})

    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']

        profile_to_nominate = Profile.objects.get(id=hi)
        profile = Profile.objects.all().get(username=self.request.user)

        has_nominated = True

        if profile.nominated_profile == profile_to_nominate:
            profile.nominated_profile = None
            profile_to_nominate.noms.remove(profile)
            has_nominated = False
        else:
            if profile.nominated_profile:
                profile.nominated_profile.noms.remove(profile)
            profile_to_nominate.noms.add(profile)
            profile.nominated_profile = profile_to_nominate

        profile.save()

        return JsonResponse({'has_nominated': has_nominated, "is_video": False})
    
    def test_func(self):
        id = self.kwargs['id']
        profile_to_nominate = Profile.objects.get(id=id)
        currentprofile = Profile.objects.filter(username=self.request.user)
        return currentprofile.exists() and currentprofile.first() != profile_to_nominate
         
class RemoveFollower(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_redirect_url(self):
        return reverse('detail-profile', kwargs={'id': self.object.id})
    
    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']
        profilething = Profile.objects.get(id=hi)
        currentprofile = Profile.objects.get(username=self.request.user)

        profilething.followers.remove(request.user)
        currentprofile.following.remove(profilething)
    
        followers_count = profilething.followers.count()

        return JsonResponse({'follow_count': followers_count})
    
    def test_func(self):
        hi = self.kwargs['id']
        profilething = Profile.objects.get(id=hi)
        currentprofile = Profile.objects.filter(username=self.request.user)
        return currentprofile.exists() and currentprofile.first() != profilething

class DetailChat(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    paginate_by = 20
    def get(self, request, *args, **kwargs):
        e = self.kwargs['id']
        form = MessageForm()
        requestprofile = Profile.objects.all().get(username=request.user)
        profile = Profile.objects.all().get(id=e)
        if requestprofile.chats.filter(members__in=[profile]).exists():
            pen = requestprofile.chats.filter(members__in=[profile]).latest("date_made")
        else:
            pen = Chat.objects.create()
            pen.save()
            pen.members.add(requestprofile)
            pen.members.add(profile)
            profile.chats.add(pen)
            requestprofile.chats.add(pen)

        messages = Message.objects.filter(chat=pen).order_by('-date_sent')
        chat_count = messages.count()
        context = {
            'e': e,
            'post': pen,
            'form': form,
            'messages': messages,
            'message_amount': chat_count,
        }
        messages.filter(read=False).filter(sender=profile).update(read=True)

        return render(request, 'profiles/detail_chat.html', context)

    def post(self, request, *args, **kwargs):
        e = self.kwargs['id']
        profile = Profile.objects.all().get(username=request.user)
        pen = profile.chats.filter(members__in=[Profile.objects.get(id=e)]).latest("date_made")
        form = MessageForm(request.POST)

        last_message_time = cache.get(f"last_message_{self.request.user.id}")

        if last_message_time and datetime.now() < last_message_time + timedelta(seconds=15):
            form.add_error(None, "Message didn't send due to 15 second cooldown")

        elif form.is_valid():
            new_message = form.save(commit=False)
            new_message.sender = Profile.objects.get(username=request.user)
            new_message.chat = pen
            new_message.save()
            pen.messages.add(new_message)

            cache.set(f"last_message_{self.request.user.id}", datetime.now(), timeout=None)

            return redirect(f'{reverse("chat-detail", kwargs={"id": e})}')

        messages = Message.objects.filter(chat=pen).order_by('-date_sent')

        context = {
            'e': e,
            'post': pen,
            'form': form,
            'messages': messages,
        }
        return render(request, 'profiles/detail_chat.html', context)
    
    def test_func(self):
        hi = self.kwargs['id']
        profilething = Profile.objects.get(id=hi)
        currentprofile = Profile.objects.get(username=self.request.user)
        following_eachother = profilething.followers.contains(currentprofile.username) and currentprofile.followers.contains(profilething.username)
        return currentprofile != profilething and (following_eachother or currentprofile.username.is_superuser or profilething.chats.filter(members__in=[currentprofile]).exists())

class ChatIndex(ListView):
    model = Chat
    template_name = "profiles/index_chats.html"
    paginate_by = 20

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryset = Chat.objects.all().filter(members__in=[Profile.objects.get(username=self.request.user)]).distinct().alias(max_date_sent=Max('messages__date_sent'))

        if sort_by == 'date-desc':
            queryset = queryset.order_by("-max_date_sent")
        elif sort_by == 'date-asc':
            queryset = queryset.order_by("max_date_sent")
        else:
            queryset = queryset.order_by("-max_date_sent")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort-by')
        return context

class ShadowBan(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_redirect_url(self):
        return reverse('detail-profile', kwargs={'id': self.object.id})
    
    def get(self, request, *args, **kwargs):
        hi = self.kwargs['id']
        profile = Profile.objects.get(id=hi)
        profile.shadowbanned = not profile.shadowbanned
        profile.save()

        return redirect(reverse('detail-profile', kwargs={'id': hi}))
    
    def test_func(self):
        hi = self.kwargs['id']
        profilething = Profile.objects.get(id=hi)
        currentprofile = Profile.objects.get(username=self.request.user)
        return (currentprofile != profilething) and currentprofile.username.is_superuser and not profilething.username.is_superuser

class AppealBan(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = BanAppeal
    fields = ['appeal_message']
    template_name = 'profiles/ban_appeal_form.html'
    is_valid = None
    
    def get(self, request, *args, **kwargs):
        profile = Profile.objects.all().get(username=self.request.user)
        ban = Ban.objects.all().get(profile=profile)
        form = BanAppealForm()

        return render(self.request, 'profiles/ban_appeal_form.html', {"form": form, "ban": ban})
    
    def post(self, request, *args, **kwargs):
        profile = Profile.objects.all().get(username=self.request.user)
        ban = Ban.objects.all().get(profile=profile)
        form = BanAppealForm(request.POST)

        appeal = form.save(commit=False)
        appeal.number = ban.appeals.all().count() + 1
        appeal.ban = ban
        appeal.save()

        ban.appeals.add(appeal)

        return render(self.request, 'profiles/ban_appeal_sent.html', {"form": form, "ban": ban})
    
    def test_func(self):
        profile = Profile.objects.all().get(username=self.request.user)
        ban = Ban.objects.all().filter(profile=profile)

        if not ban.exists():
            return False

        return can_appeal(ban.first()) == True
    
def ban_page(request):
    profile = Profile.objects.all().get(username=request.user)
    ban = Ban.objects.all().filter(profile=profile)

    if not ban.exists():
        return redirect('index')

    context = {
        "ban": ban.first()
    }

    return render(request, "profiles/ban_page.html", context)

class CreateBan(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Ban
    fields = ['given_reason', 'description', 'delete_all_creations']
    template_name = 'profiles/create_ban.html'
    is_valid = None
    
    def form_valid(self, form):
        banned_profile = Profile.objects.all().get(id=self.kwargs["id"])

        form.instance.ban_giver = Profile.objects.all().get(username=self.request.user)
        form.instance.profile = banned_profile

        banned_profile.banned = True

        if "delete_all_creations" in form.data:
            banned_profile.videos.all().delete()
            banned_profile.comments.all().delete()
            banned_profile.chats.all().delete()
            banned_profile.delete_media()
            banned_profile.remove_follows()
            ProfileRating.objects.all().filter(rater=banned_profile.username).delete()
            ProfileRating.objects.all().filter(rated_profile=banned_profile).delete()
            ProfileCustomisation.objects.all().filter(customised_profile=banned_profile).delete()

        form.instance.delete_all_creations = False

        banned_profile.save()
        form.save()

        return super().form_valid(form)
        
    def test_func(self):
        ban_profile = Profile.objects.all().filter(id=self.kwargs["id"])
        profile = Profile.objects.all().filter(username=self.request.user)

        if not profile.exists() or not ban_profile.exists():
            return False
        
        ban_profile = ban_profile.first()
        
        return self.request.user != ban_profile.username and self.request.user.is_superuser and not ban_profile.username.is_superuser
    
    def get_success_url(self):
        return reverse('index')
    
class RemoveBan(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ban
    template_name = 'profiles/remove_ban.html'
    slug_url_kwarg = "id"
    slug_field = "id"
    def get_redirect_url(self):
        return reverse('detail-profile', kwargs={'id': self.object.profile.id})

    def get_success_url(self):
        ban = self.get_object()

        ban.profile.banned = False
        ban.profile.save()

        return reverse('detail-profile', kwargs={'id': ban.profile.id})
        
    def test_func(self):
        return self.request.user.is_superuser
    
class RejectBanAppeal(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = BanAppeal

    def get(self, request, *args, **kwargs):
        id = self.kwargs['id']
        num = self.kwargs['num']
        appeal = BanAppeal.objects.filter(ban__profile__id=id).get(number=num)

        context = {
            'appeal': appeal,
        }

        return render(request, 'profiles/reject_ban_appeal.html', context)
    
    def post(self, request, *args, **kwargs):
        id = self.kwargs['id']
        num = self.kwargs['num']
        appeal = BanAppeal.objects.filter(ban__profile__id=id).get(number=num)
        appeal.rejected = True
        appeal.save()

        return redirect('ban-appeals')
        
    def test_func(self):
        return self.request.user.is_superuser

def admin_page(request):
    if not request.user.is_superuser:
        return render(request, '403.html')
    
    profile = Profile.objects.all().get(username=request.user)

    context = {
        "profile": profile
    }

    return render(request, "profiles/admin_tools.html", context)

class BanAppealIndex(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = BanAppeal
    template_name = 'profiles/index_ban_appeals.html'
    paginate_by = 9

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        
        appeals = BanAppeal.objects.all()
        queryset = appeals.filter(rejected=False) | appeals.filter(rejected=True)

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
            )
        else:
            queryset = sorted(
                queryset,
                key=attrgetter('date_made'),
                reverse=True
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort-by')
        return context
    
    def test_func(self):
        return self.request.user.is_superuser
    
class DetailBanAppeal(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        id = self.kwargs['id']
        num = self.kwargs['num']
        appeal = BanAppeal.objects.filter(ban__profile__id=id).get(number=num)

        context = {
            'appeal': appeal,
        }

        return render(request, 'profiles/detail_ban_appeal.html', context)