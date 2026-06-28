from django import forms
from .models import Comment

# the idea here is when an admin deletes a video, comment, etc, they can notify the creator
# without having to message them 
class AdminDeleteObjectForm(forms.Form):
    notify = forms.BooleanField()
    notification_message = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'rows': '2',
            'placeholder': 'Write a notification message, e.g. "Please try to avoid contentious topics like religion on Glomble"',
            'maxlength': '100',
        })
    )

class CommentForm(forms.ModelForm):
    comment = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'rows': '3',
            'placeholder': 'Input the text you want to comment!',
            'maxlength': '500',
        })
    )

    class Meta:
        model = Comment

        fields = ['comment']

class ReplyForm(forms.ModelForm):
    comment = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'rows': '3',
            'placeholder': 'Input the text you want to reply!',
            'maxlength': '500',
        })
    )

    class Meta:
        model = Comment

        fields = ['comment']