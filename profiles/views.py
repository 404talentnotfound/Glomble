from django.shortcuts import render, reverse, redirect
from .models import Profile, Chat, Message, ProfileCustomisation, ProfileRating
import random
from videos.models import Video
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, DeleteView
from django.contrib.auth.models import User
from django.views import View
from django.db.models import Q, Count, Max
from .forms import UserRegisterForm, CreateProfileForm, MessageForm, ProfileCustomisationForm, ProfileRatingForm
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
from Glomble.pc_prod import *
from django.contrib.auth.tokens import default_token_generator
import magic
import tempfile
import subprocess
from django.core.cache import cache
from notifications.models import MilestoneNotification
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import EmailMessage

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
                try:
                    client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=f"profiles/banners/{customised_profile.customisation.banner_image.name}")
                except:
                    pass

                banner = request.FILES['banner_image']
                form.save(commit=False)
                temp_banner = tempfile.NamedTemporaryFile(delete=False)
                for chunk in banner.chunks():
                    temp_banner.write(chunk)
                form.instance.banner_image = f"profiles/banners/{customised_profile.id}-{random_id}.png"

                subprocess.run(f"ffmpeg -y -i {temp_banner.name} {customised_profile.id}.png", shell=True, check=True)

                with open(f'{customised_profile.id}.png') as pfp_file:
                    client.upload_fileobj(
                        pfp_file.buffer,
                        AWS_STORAGE_BUCKET_NAME,
                        f"profiles/banners/{customised_profile.id}-{random_id}.png",
                        ExtraArgs={"ContentType": 'image/png'},
                    )

                temp_banner.close()

                os.remove(f"{customised_profile.id}.png")
                os.remove(temp_banner.name)
                    
            if 'video_banner' in request.FILES:
                try:
                    client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=f"{customised_profile.customisation.video_banner.name}")
                except:
                    pass

                banner = request.FILES['video_banner']
                form.save(commit=False)
                temp_banner = tempfile.NamedTemporaryFile(delete=False)
                for chunk in banner.chunks():
                    temp_banner.write(chunk)
                form.instance.video_banner = f"profiles/video_banners/{customised_profile.id}-{random_id}.png"

                subprocess.run(f"ffmpeg -y -i {temp_banner.name} -vf scale=256:220 {customised_profile.id}.png", shell=True, check=True)

                with open(f'{customised_profile.id}.png') as pfp_file:
                    client.upload_fileobj(
                        pfp_file.buffer,
                        AWS_STORAGE_BUCKET_NAME,
                        f"profiles/video_banners/{customised_profile.id}-{random_id}.png",
                        ExtraArgs={"ContentType": 'image/png'},
                    )

                temp_banner.close()

                os.remove(temp_banner.name)
                
            form.save()

            customised_profile.customisation = form.instance
            customised_profile.save()

            return redirect('detail-profile', id=id)
    else:
        form = ProfileCustomisationForm(instance=customisation)
    
    return render(request, 'profiles/customise_profile.html', {'form': form, 'customised_profile': customised_profile})


def update_profile_follow_count(request, id):
    follow_count = Profile.objects.get(id=id).followers.count()
    return JsonResponse({"follow_count": follow_count})

@user_not_authenticated
def resend_activation(req, id):
    user = User.objects.all().get(id=id)
    activateEmail(req, user, user.email)
    return redirect("login")

def redirect_profile(request, id):
    return redirect(f"{reverse('detail-profile', kwargs={'id': id})}")

class ProfileIndex(ListView):
    model = Profile
    template_name = "profiles/index.html"
    paginate_by = 20

    def get_queryset(self):
        sort_by = self.request.GET.get('sort-by')
        queryset = Profile.objects.all()
        query = self.request.GET.get('query')
        queryset = queryset.annotate(num_followers=Count('followers'))

        if query:
            queryset = queryset.filter(Q(username__username__icontains=query))

        if sort_by == 'date-desc':
            queryset = queryset.order_by('-date_made')
        elif sort_by == 'date-asc':
            queryset = queryset.order_by('date_made')
        elif sort_by == 'followers-desc':
            queryset = queryset.order_by('-num_followers')
        elif sort_by == 'ratings':
            queryset = queryset.order_by('-rating', '-num_followers')
        else:
            queryset = queryset.order_by('-num_followers')
        queryset = queryset.exclude(shadowbanned=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort-by')
        context['query'] = self.request.GET.get('query')
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
    messages.success(request, f"Hello {user}, please go to your email {to_email} inbox and click on \
        the activation link to confirm and complete the registration. Note: If you can't find the email, check your spam folder.")

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

# dear lord this shit sucks ass I really need to rewrite this
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
                if form.is_valid() and pfp.size < 5000000 and pfp.size > 1024:
                    mime_type = magic.Magic(mime=True).from_buffer(pfp.read(1024))
                    if mime_type in ['image/jpeg', 'image/png']:
                        form.save(commit=False)
                        temp_pfp = tempfile.NamedTemporaryFile(delete=False)
                        for chunk in pfp.chunks():
                            temp_pfp.write(chunk)
                        form.instance.profile_picture = f"profiles/pfps/{out}.png"

                        subprocess.run(f"ffmpeg -y -i {temp_pfp.name} -vf scale=512:512 {profile.id}.png", shell=True, check=True)

                        with open(f'{profile.id}.png') as pfp_file:
                            client.upload_fileobj(
                                pfp_file.buffer,
                                AWS_STORAGE_BUCKET_NAME,
                                f"profiles/pfps/{profile.id}.png",
                                ExtraArgs={"ContentType": 'image/png'},
                            )

                        temp_pfp.close()

                        os.remove(f'{profile.id}.png')
                        os.remove(temp_pfp.name)

                        form.save()

                        return redirect('profile-page')
                    else:
                        form.add_error(None, "An error occurred while making your profile. Please make sure the profile picture the correct format (png or jpg) and try again.")
                        return redirect('create-profile')
                else:
                    form.add_error(None, "An error occurred while making your profile. Please make sure the profile picture is under 10mb and over 1kb, then try again.")
                    return redirect('create-profile')
            else:
                form.instance.profile_picture.name = "profiles/pfps/default.png"
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
        if (request.user.is_superuser or profile.moderator) or username == request.user:
            posts = profile.videos.all().order_by("-date_posted")
        else:
            posts = profile.videos.all().exclude(unlisted=True).order_by("-date_posted")
        followers = profile.followers.all()
        follow_num = len(followers)
        developer = False
        creator = False
        supporter = False
        developers = DEVELOPER_IDS
        creators = CREATOR_ID
        if poopie in developers:
            developer = True
        if poopie in creators:
            creator = True

        if follow_num == 0:
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
            'object_list': posts,
            'follow_num': follow_num,
            'is_following': is_following,
            'developer': developer,
            'creator': creator,
            'supporter': supporter,
            'profile': profile,
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
        last_upload_time = cache.get(f"last_profileupdate_{self.request.user.id}")

        if last_upload_time is not None and datetime.now() < last_upload_time + timedelta(minutes=1):
            form.add_error(None, "You can only update your profile every minute.")
            return super().form_invalid(form)

        if form.is_valid():
            try:
                if 'profile_picture' in self.request.FILES:
                    newpfp = self.request.FILES['profile_picture']
                    if form.is_valid() and newpfp.size < 5000000 and newpfp.size > 1024:
                        mime_type = magic.Magic(mime=True).from_buffer(newpfp.read(1024))
                        if mime_type in ['image/jpeg', 'image/png']:
                            temp_pfp = tempfile.NamedTemporaryFile(delete=False)
                            for chunk in newpfp.chunks():
                                temp_pfp.write(chunk)
                            try:
                                if profile.profile_picture.name != "profiles/pfps/default.png":
                                    try:
                                        client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=f"profiles/banners/{profile.profile_picture.name}")
                                    except:
                                        pass
                            except Exception as e:
                                pass

                            cache.set(f"last_profileupdate_{self.request.user.id}", datetime.now(), timeout=None)

                            subprocess.run(f"ffmpeg -y -i {temp_pfp.name} -vf scale=512:512 {profile.id}.png", shell=True, check=True)

                            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
                            random_id = "".join(random.choice(chars) for _ in range(5))

                            form.instance.profile_picture = f"profiles/pfps/{profile.id}-{random_id}.png"

                            with open(f'{profile.id}.png') as pfp_file:
                                client.upload_fileobj(
                                    pfp_file.buffer,
                                    AWS_STORAGE_BUCKET_NAME,
                                    f"profiles/pfps/{profile.id}-{random_id}.png",
                                    ExtraArgs={"ContentType": 'image/png'},
                                )

                            temp_pfp.close()

                            os.remove(f"{profile.id}.png")
                            os.remove(temp_pfp.name)

                            return super().form_valid(form)
                        else:
                            form.add_error(None, "An error occurred while making your profile. Please make sure the profile picture the correct format (png or jpg) and try again.")
                            return super().form_invalid(form)
                    else:
                        form.add_error(None, "An error occurred while making your profile. Please make sure the profile picture is under 10mb and over 1kb, then try again.")
                        return super().form_invalid(form)
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
        try:
            if Profile.objects.all().get(id=self.object.id).profile_picture.name != "media/profiles/pfps/default.png":
                try:
                    client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=f"profiles/banners/{profile.profile_picture.name}")
                except:
                    pass
        except:
            pass

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
        if request.user != profilething.username:
            profilething.followers.add(request.user)
        
        followers_count = profilething.followers.count()

        if (followers_count in MILESTONES) and followers_count > profilething.follower_milestones:
            profilething.follower_milestones = followers_count
            profilething.save()
            MilestoneNotification.objects.create(profile=profilething, message=f"Your profile reached a follower milestone of {followers_count} people!")

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

        if profile.chats.filter(members__in=[profilething]).exists():
            profile.chats.get(members__in=[profilething]).delete()

        return JsonResponse({'follow_count': followers_count})
    
    def test_func(self):
        hi = self.kwargs['id']
        profilething = Profile.objects.get(id=hi)
        currentprofile = Profile.objects.get(username=self.request.user)
        return currentprofile != profilething

class DetailChat(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    paginate_by = 20
    def get(self, request, *args, **kwargs):
        e = self.kwargs['id']
        form = MessageForm()
        profile = Profile.objects.all().get(username=request.user)
        if profile.chats.filter(members__in=[Profile.objects.get(id=e)]).exists():
            pen = profile.chats.filter(members__in=[Profile.objects.get(id=e)]).latest("date_made")
        else:
            pen = Chat.objects.create()
            pen.save()
            pen.members.add(Profile.objects.get(username=request.user))
            pen.members.add(Profile.objects.get(id=e))
            Profile.objects.get(id=e).chats.add(pen)
            Profile.objects.get(username=request.user).chats.add(pen)

        messages = Message.objects.filter(chat=pen).order_by('-date_sent')
        chat_count = messages.count()
        context = {
            'e': e,
            'post': pen,
            'form': form,
            'messages': messages,
            'message_amount': chat_count,
        }
        for i in messages.exclude(read=True):
            if i.sender != Profile.objects.get(username=request.user):
                i.read = True
                i.save()

        return render(request, 'profiles/detail_chat.html', context)

    def post(self, request, *args, **kwargs):
        e = self.kwargs['id']
        profile = Profile.objects.all().get(username=request.user)
        pen = profile.chats.filter(members__in=[Profile.objects.get(id=e)]).latest("date_made")
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
