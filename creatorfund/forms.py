from .models import Creator
from django import forms

class UpdateCreatorForm(forms.ModelForm):
    class Meta:
        model = Creator

        fields = ['paypal_email']