from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Message, BanAppeal
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django import forms
from .models import ProfileCustomisation
from django.core.validators import MaxValueValidator, MinValueValidator
import re

class ProfileCustomisationForm(forms.ModelForm):
    class Meta:
        model = ProfileCustomisation
        fields = ['use_text_shadow', 'use_video_card_text_shadow', 'background_color', 'accent_color', 'text_color', 'text_shadow_color', 'video_card_text_color', 'video_card_text_shadow_color', 'banner_image', 'video_banner']
        widgets = {
            'background_color': forms.TextInput(attrs={'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color'}),
            'text_color': forms.TextInput(attrs={'type': 'color'}),
            'text_shadow_color': forms.TextInput(attrs={'type': 'color'}),
            'video_card_text_color': forms.TextInput(attrs={'type': 'color'}),
            'video_card_text_shadow_color': forms.TextInput(attrs={'type': 'color'}),
        }

class ProfileRatingForm(forms.Form):
    rating = forms.IntegerField(
        label="Rate this profile",
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        widget=forms.Select(choices=[(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(6)])
    )

def validate_email(value, should_exist):
    try:
        address, domain = value.split('@')[:2]
        address = re.match(r"[^+]*", address)[0]
        address = address.replace('.', '')
        email = address+"@"+domain

    except:
        raise ValidationError("An error occured validating the email.")
    
    if User.objects.filter(email = email).exists():
        if should_exist:
            return
        raise ValidationError((f"{email} is taken."), params = {'email':email})

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

        help_texts = {
            'username': "20 characters or fewer, please do not use your email here.",
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        validate_email(email, False)
        return email
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].validators.append(MaxLengthValidator(20))

class ResendEmailForm(forms.Form):
    email = forms.EmailField(required=False)
    username = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('email') and not cleaned_data.get('username'):
            raise ValidationError({'email': 'Please fill in either the email or username.'})

    def clean_email(self):
        email = self.cleaned_data['email']
        if email:
            validate_email(email, True)
            return email

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["profile_picture", "bio"]

class CreateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile

        fields = ['profile_picture', 'bio']

class BanAppealForm(forms.ModelForm):
    appeal_message = forms.TextInput()

    class Meta:
        model = BanAppeal

        fields = ['appeal_message']


class MessageForm(forms.ModelForm):
    message = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'rows': '3',
            'placeholder': 'Say something to this creator.',
            'maxlength': '1000',
        })
    )

    class Meta:
        model = Message

        fields = ['message']
