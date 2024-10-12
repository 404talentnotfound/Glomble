from django.shortcuts import render, reverse, redirect
from .models import Profile, Chat, Message, ProfileActivity
from django.utils.html import strip_tags
import random
from videos.models import Video
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.views import View
from django.db.models import Q, Count, Max
from .forms import UserRegisterForm, CreateProfileForm, MessageForm
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
import os
from datetime import datetime, timedelta
import sendgrid
from sendgrid.helpers.mail import *
from Glomble.pc_prod import *
from django.contrib.auth.tokens import default_token_generator
import magic
import tempfile
import subprocess
from django.core.cache import cache
from notifications.models import FollowNotification

def update_profile_follow_count(request, id):
    follow_count = Profile.objects.get(id=id).followers.count()
    return JsonResponse({"follow_count": follow_count})

def redirect_profile(request, id):
    return redirect(f"{reverse('detail-profile', kwargs={'id': id})}")

def toggle_tracking_activity(request):
    profile = Profile.objects.get(username=request.user)
    profile.using_activity = not profile.using_activity
    if profile.using_activity:
        if not ProfileActivity.objects.filter(profile=profile).exists():
            activity = ProfileActivity.objects.create(profile=profile)
        else:
            activity = ProfileActivity.objects.get(profile=profile)
        profile.activity = activity
    profile.save()
    return redirect(f"{reverse('detail-profile', kwargs={'id': profile.id})}")

class ProfileIndex(ListView):
    model = Profile
    template_name = "profiles/index.html"
    paginate_by = 8

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryset = Profile.objects.all()
        queryset = queryset.annotate(num_followers=Count('followers'))

        if sort_by == 'date-desc':
            queryset = queryset.order_by('-date_made')
        elif sort_by == 'date-asc':
            queryset = queryset.order_by('date_made')
        elif sort_by == 'followers-desc':
            queryset = queryset.order_by('-num_followers')
        else:
            queryset = queryset.order_by('-num_followers')
        excluded_profiles = ['.']
        queryset = queryset.exclude(username__username__in=excluded_profiles)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort-by')
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

        messages.success(request, "Thank you for your email confirmation. Now you can login your account.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid!")

class CreateProfile(LoginRequiredMixin, CreateView):
    model = Profile
    fields = ['profile_picture', 'bio']
    template_name = "profiles/create-profile.html"
    def form_valid(self, form):
        if Profile.objects.filter(username=self.request.user).exists():
            raise ValidationError("you already have a profile associated with this account")
        else:
            form.instance.username = self.request.user
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            out = ""
            
            while True:
                for i in range(12):
                    out += random.choice(chars)
                if not Profile.objects.filter(id=out).exists():
                    break
                else:
                    out = ""

            form.instance.id = out
            print(out)
            return super().form_valid(form)

    def get_success_url(self):
        return reverse('detail-profile', kwargs={'id': self.object.id})

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
            return redirect("login")
    else:
        Form = UserRegisterForm()
    return render(req, "profiles/register.html", {'form': Form})

class CustomPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        email = form.cleaned_data['email']
        user = Profile.objects.all().get(username=User.objects.all().get(email=email))
        uid = urlsafe_base64_encode(force_bytes(user.username.id))
        token = default_token_generator.make_token(user.username)
        reset_url = self.request.build_absolute_uri(
            reverse('password_reset_confirm', args=[uid, token])
        )
        html_thing = render_to_string('profiles/password_reset_email.html', {"reset_url": reset_url, "user": user.username.username})
        plain_text_thing = strip_tags(html_thing)
        message = Mail(
            from_email=EMAIL_HOST_USER,
            to_emails=email,
            subject='Glomble Password Reset',
            html_content=html_thing,
        )
        sendgrid_client = sendgrid.SendGridAPIClient(api_key=EMAIL_HOST_PASSWORD)
        sendgrid_client.send(message)
        return redirect('password_reset_done')

def activateEmail(request, user, to_email):
    mail_subject = "Activate your user account."
    message = render_to_string("template_activate_account.html", {
        'user': user,
        'domain': "glomble.com",
        'uid': urlsafe_base64_encode(force_bytes(user.id)),
        'token': account_activation_token.make_token(user),
        "protocol": 'https' if request.is_secure() else 'http'
    })
    sg = sendgrid.SendGridAPIClient(api_key=EMAIL_HOST_PASSWORD)
    from_email = Email(EMAIL_HOST_USER)
    to_email_sendgrid = To(to_email)
    content = Content("text/html", message)
    mail = Mail(from_email, to_email_sendgrid, mail_subject, content)
    mail_json = mail.get()
    response = sg.client.mail.send.post(request_body=mail_json)
    if response.status_code == 202:
        messages.success(request, f"Dear {user}, please go to your email {to_email} inbox and click on \
                the activation link to confirm and complete the registration. Note: If you can't find the email, check your spam folder.")
    else:
        messages.error(request, f'Problem sending email to {to_email}, check if you typed it correctly.')

@login_required
def profile(request):
    username = request.GET.get('username', request.user)
    profile = Profile.objects.get(username=username)
    followers = profile.followers
    hi = profile.id
    info = Profile.objects.get(id=hi).bio
    pfp = Profile.objects.get(id=hi).profile_picture
    username = Profile.objects.get(id=hi).username
    poopie = Profile.objects.get(id=hi).id
    posts = Video.objects.all().order_by('-date_posted').filter(uploader=profile)
    profile = Profile.objects.get(id=poopie)
    followers = profile.followers.all()
    follow_num = len(followers)

    if len(followers) == 0:
        is_following = False

    for follower in followers:
        if follower == request.user:
            is_following = True
            break
        else:
            is_following = False

    context = {
        'info': info,
        'poopie': poopie,
        'pfp': pfp,
        'username': username,
        'detail_profile_list': posts,
        'follow_num': follow_num,
        'is_following': is_following,
    }
    return render(request, 'profiles/detail_profile.html', context)

@login_required
def create_profile(request):
    user = request.user
    has_profile = Profile.objects.filter(username=user).exists()
    if has_profile:
        return redirect('profile-page')
    
    if request.method == "POST":
        profile = Profile(username=user)
        form = CreateProfileForm(request.POST, request.FILES, instance=profile)
        try:
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            out = ""
            
            while True:
                for i in range(12):
                    out += random.choice(chars)
                if not Profile.objects.filter(id=out).exists():
                    break
                else:
                    out = ""

            form.instance.id = out
            if 'profile_picture' in request.FILES:
                pfp = request.FILES['profile_picture']
                mime_type = magic.Magic(mime=True).from_buffer(pfp.read(1024))
                if mime_type in ['image/jpeg', 'image/png']:
                    form.save(commit=False)
                    if form.is_valid() and pfp.size < 5000000 and pfp.size > 1024:
                        temp_pfp = tempfile.NamedTemporaryFile(delete=False)
                        for chunk in pfp.chunks():
                            temp_pfp.write(chunk)
                        form.instance.profile_picture = f"media/profiles/pfps/{out}.png"

                        subprocess.run(f"ffmpeg -y -i {temp_pfp.name} -vf scale=512:512 'media/profiles/pfps/{profile.id}.png'", shell=True, check=True)

                        os.remove(temp_pfp.name)

                        form.save()

                        return redirect('profile-page')
                    else:
                        form.add_error(None, "An error occurred while making your profile. Please make sure the profile picture is under five megabytes and try again.")
                        return redirect('create-profile')
                else:
                    form.add_error(None, "An error occurred while making your profile. Please make sure the profile picture the correct format and try again.")
                    return redirect('create-profile')
            else:
                form.instance.profile_picture.name = "media/profiles/pfps/default.png"
                if form.is_valid():
                    form.save()
                    return redirect('profile-page')
        except:
            if form.is_valid():
                form.save()
                return redirect('profile-page')
    else:
        form = CreateProfileForm()
    
    context = {
        'form': form
    }
    return render(request, "profiles/create_profile.html", context)

class DetailProfileIndex(ListView):
    model = Profile
    slug_url_kwarg = "id"
    slug_field = "id"
    template_name = 'profiles/detail_profile.html'
    def get(self, request, *args, **kwargs):
        hi = self.kwargs['id']
        info = Profile.objects.get(id=hi).bio
        pfp = Profile.objects.get(id=hi).profile_picture
        username = Profile.objects.get(id=hi).username
        poopie = Profile.objects.get(id=hi).id
        profile = Profile.objects.get(id=poopie)
        if request.user.is_superuser or username == request.user:
            posts = Video.objects.all().order_by('-date_posted').filter(uploader=profile)
        else:
            posts = Video.objects.all().order_by('-date_posted').filter(uploader=profile).exclude(unlisted=True)
        followers = profile.followers.all()
        follow_num = len(followers)
        admin = username.is_superuser
        developer = False
        creator = False
        developers = DEVELOPER_IDS
        creators = CREATOR_ID
        if poopie in developers:
            developer = True
        if poopie == creators:
            creator = True

        if len(followers) == 0:
            is_following = False

        for follower in followers:
            if follower == request.user:
                is_following = True
                break
            else:
                is_following = False

        context = {
            'info': info,
            'poopie': poopie,
            'pfp': pfp,
            'username': username,
            'detail_profile_list': posts,
            'follow_num': follow_num,
            'is_following': is_following,
            'admin': admin,
            'developer': developer,
            'creator': creator,
        }
        return render(request, 'profiles/detail_profile.html', context)

class UpdateProfile(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Profile
    slug_url_kwarg = "id"
    slug_field = "id"
    fields = ['profile_picture','bio']
    template_name = "profiles/update_profile.html"
    def form_valid(self, form):
        profile = Profile.objects.get(id=self.kwargs['id'])
        cooldown_valid = True
        last_upload_time = cache.get(f"last_profileupdate_{self.request.user.id}")

        if last_upload_time is not None and datetime.now() < last_upload_time + timedelta(minutes=1):
            form.add_error(None, "You can only update your profile every minute.")
            cooldown_valid = False
            return super().form_invalid(form)

        if form.is_valid():
            try:
                if 'profile_picture' in self.request.FILES:
                    newpfp = self.request.FILES['profile_picture']
                    mime_type = magic.Magic(mime=True).from_buffer(newpfp.read(1024))
                    
                    if mime_type in ['image/jpeg', 'image/png']:
                        if 1024 < newpfp.size < 10000000:
                            temp_pfp = tempfile.NamedTemporaryFile(delete=False)
                            for chunk in newpfp.chunks():
                                temp_pfp.write(chunk)
                            try:
                                if profile.profile_picture.name != "media/profiles/pfps/default.png":
                                    os.remove(f'media/profiles/pfps/{profile.id}.png')
                            except Exception as e:
                                print(e)

                            cache.set(f"last_profileupdate_{self.request.user.id}", datetime.now(), timeout=None)

                            subprocess.run(f"ffmpeg -y -i {temp_pfp.name} -vf scale=512:512 media/profiles/pfps/{profile.id}.png", shell=True, check=True)

                            form.instance.profile_picture = f"media/profiles/pfps/{profile.id}.png"

                            os.remove(temp_pfp.name)

                            return super().form_valid(form)
                        
                        else:
                            form.add_error(None, "An error occurred while updating your profile. Please make sure the profile picture is under 10 megabytes and try again.")
                            return super().form_invalid(form)
                    else:
                        form.add_error(None, "An error occurred while making your profile. Please make sure the profile picture the correct format and try again.")
                        return super().form_invalid(form)
                else:
                    form.instance.profile_picture.name = 'media/profiles/pfps/default.png'
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
        return self.request.user == profile.username or (self.request.user.is_superuser and profile.id != CREATOR_ID)

class DeleteProfile(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Profile
    template_name = 'profiles/delete_profile.html'
    slug_url_kwarg = "id"
    slug_field = "id"
    def get_redirect_url(self):
        return reverse('detail-profile', kwargs={'id': self.object.id})

    def get_success_url(self):
        profile = self.get_object()
        try:
            os.remove(Profile.objects.all().get(id=self.object.id).profile_picture.name)
        except:
            pass
        for video in Video.objects.filter(uploader=profile):
            os.remove(video.video_file.name)
        Video.objects.filter(uploader=profile).delete()
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
        if request.user != profilething.username:
            profilething.followers.add(request.user)

        profile = Profile.objects.get(username=request.user)

        if profile.using_activity:
            ProfileActivity.objects.get(profile=profile).followed_profiles.add(profilething)
        
        followers_count = profilething.followers.count()

        milestones = [5, 10, 25, 50, 100]

        if (followers_count in milestones) and followers_count > profilething.passed_milestones:
            profilething.passed_milestones = followers_count
            profilething.save()
            FollowNotification.objects.create(profile=profilething)

        return JsonResponse({'follow_count': followers_count})
    
    def test_func(self):
        hi = self.kwargs['id']
        profilething = Profile.objects.get(id=hi)
        currentprofile = Profile.objects.get(username=self.request.user)
        return currentprofile != profilething
         
class RemoveFollower(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_redirect_url(self):
        return reverse('detail-profile', kwargs={'id': self.object.id})
    
    def post(self, request, *args, **kwargs):
        hi = self.kwargs['id']
        profilething = Profile.objects.get(id=hi)
        if profilething.id != 5:
            if request.user != profilething.username:
                profilething.followers.remove(request.user)
    
        followers_count = profilething.followers.count()

        profile = Profile.objects.get(username=request.user)

        if ProfileActivity.objects.filter(profile=profile).exists():
            ProfileActivity.objects.get(profile=profile).followed_profiles.remove(profilething)

        return JsonResponse({'follow_count': followers_count})
    
    def test_func(self):
        hi = self.kwargs['id']
        profilething = Profile.objects.get(id=hi)
        currentprofile = Profile.objects.get(username=self.request.user)
        return currentprofile != profilething

class UserSearch(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('query')
        print(query)
        excluded_profiles = ['.']
        profile_list = Profile.objects.filter(
        	Q(username__username__icontains=query)
        ).exclude(username__username__in=excluded_profiles)

        profile = Profile.objects.get(username=self.request.user)
        if profile.using_activity:
            profile_activity = ProfileActivity.objects.get(profile=profile)
            profile_activity.searches += query + "\n"
            profile_activity.save()
    
        context = {
        	'profile_list': profile_list
        }
    

        return render(request, 'profiles/search.html', context)

class DetailChat(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    
    def get(self, request, *args, **kwargs):
        e = self.kwargs['id']
        form = MessageForm()
        if Chat.objects.all().filter(members__in=[Profile.objects.get(username=request.user)]).filter(members__in=[Profile.objects.get(id=e)]).exists():
            pen = Chat.objects.all().filter(members__in=[Profile.objects.get(username=request.user)]).filter(members__in=[Profile.objects.get(id=e)]).latest("date_made")
        else:
            pen = Chat.objects.create()
            pen.save()
            pen.members.add(Profile.objects.get(username=request.user))
            pen.members.add(Profile.objects.get(id=e))

        messages = Message.objects.filter(chat=pen).order_by('-date_sent')
        chat_count = messages.count()
        context = {
            'e': e,
            'post': pen,
            'form': form,
            'messages': messages,
            'message_amount': chat_count,
        }
        for i in messages:
            if i.sender != Profile.objects.get(username=request.user):
                i.read = True
                i.save()

        return render(request, 'profiles/detail_chat.html', context)

    def post(self, request, *args, **kwargs):
        e = self.kwargs['id']
        pen = Chat.objects.all().filter(members__in=[Profile.objects.get(username=self.request.user)]).filter(members__in=[Profile.objects.get(id=e)]).latest("date_made")
        form = MessageForm(request.POST)

        if form.is_valid():
            new_message = form.save(commit=False)
            new_message.sender = Profile.objects.get(username=request.user)
            new_message.chat = pen
            new_message.save()
            pen.messages.add(new_message)

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
        return currentprofile != profilething and following_eachother
    
class ChatIndex(ListView):
    model = Chat
    template_name = "profiles/index_chats.html"
    paginate_by = 9

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryset = Chat.objects.all()

        queryset = queryset.filter(members__in=[Profile.objects.get(username=self.request.user)]).distinct().alias(max_date_sent=Max('messages__date_sent'))

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