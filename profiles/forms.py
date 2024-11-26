from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Message
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator


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
        fields = "__all__"
        exclude = ["date_made", "followers"]

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
