from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Message
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django import forms
from .models import ProfileCustomisation
from django.core.validators import MaxValueValidator, MinValueValidator

class ProfileCustomisationForm(forms.ModelForm):
    class Meta:
        model = ProfileCustomisation
        fields = ['background_color', 'text_color', 'text_shadow_color', 'banner_image', 'video_banner']
        widgets = {
            'background_color': forms.TextInput(attrs={'type': 'color'}),
            'text_color': forms.TextInput(attrs={'type': 'color'}),
            'text_shadow_color': forms.TextInput(attrs={'type': 'color'}),
        }

class ProfileRatingForm(forms.Form):
    rating = forms.IntegerField(
        label="Rate this profile",
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        widget=forms.Select(choices=[(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(6)])
    )

def validate_email(value):
    if User.objects.filter(email = value).exists():
        raise ValidationError((f"{value} is taken."),params = {'value':value})

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

        help_texts = {
            'username': "Required. 20 characters or fewer. Letters, digits and @/./+/-/_ only.",
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        validate_email(email)
        return email
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].validators.append(MaxLengthValidator(20))

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["profile_picture", "bio"]

class CreateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile

        fields = ['profile_picture', 'bio']

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
