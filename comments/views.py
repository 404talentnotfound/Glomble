from django.shortcuts import reverse, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import DeleteView, UpdateView
from django.http import JsonResponse
from videos.models import Comment
from videos.forms import AdminDeleteObjectForm
from notifications.models import BaseNotification, MiscellaneousNotification, send_misc_notification
from profiles.models import Profile
from django.shortcuts import render

class PinComment(LoginRequiredMixin, UserPassesTestMixin, View):
	def get_redirect_url(self):
		return reverse('video-detail', kwargs={'id': self.object.post.id})

	def get(self, request, *args, **kwargs):
		hi = self.kwargs['pk']
		comment = Comment.objects.get(pk=hi)
		video = comment.post

		if video.pinned_comment == comment:
			video.pinned_comment = None
			video.save()

			return redirect(reverse('video-detail', kwargs={'id': video.id}))

		video.pinned_comment = comment
		video.save()

		if comment.commenter.username != request.user:
			send_misc_notification([comment.commenter], comment=comment, message=f'{video.uploader.username} just pinned your comment: "{comment.comment}"')

		return redirect(reverse('video-detail', kwargs={'id': video.id})+f'#comment={comment.pk}')
	
	def test_func(self):
		comment = Comment.objects.all().get(pk=self.kwargs['pk'])
		return self.request.user == comment.post.uploader.username and comment.replying_to == None

class DeleteComment(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = Comment
	template_name = 'videos/comment_delete.html'

	def get_redirect_url(self):
		return reverse('video-detail', kwargs={'id': self.object.post.id})

	def get_success_url(self):
		return reverse('video-detail', kwargs={'id': self.object.post.id})
	
	def post(self, request, *args, **kwargs):
		comment = self.get_object()
		form = AdminDeleteObjectForm(request.POST)

		if not request.user.is_superuser or request.user == comment.commenter.username:
			return super().delete(request, *args, **kwargs)
		
		if form.is_valid() and form.cleaned_data["notify"]:
			send_misc_notification([comment.commenter], message=f"Your comment was deleted \"{form.cleaned_data['notification_message']}\"")

		return super().delete(request, *args, **kwargs)
        
	def get(self, request, *args, **kwargs):
		form = AdminDeleteObjectForm()

		context = {
		    "form": form,
		}

		return render(request, 'videos/delete_video.html', context)
	
	def test_func(self):
		comment = self.get_object()
		is_commenter = self.request.user == comment.commenter.username
		is_uploader = self.request.user == comment.post.uploader.username
		return is_commenter or is_uploader or self.request.user.is_superuser

class UpdateComment(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = Comment
	fields = ['comment']
	template_name = 'videos/update_comment.html'

	def get_redirect_url(self):
		return reverse('video-detail', kwargs={'id': self.object.post.id})

	def get_success_url(self):
		return reverse('video-detail', kwargs={'id': self.object.post.id})
	
	def test_func(self):
		comment = self.get_object()
		return self.request.user == comment.commenter.username or self.request.user.is_superuser

class AddLike(LoginRequiredMixin, UserPassesTestMixin, View):
	def get_redirect_url(self):
		return reverse('video-detail', kwargs={'pk': self.object.post.id})
	
	def test_func(self):
		return Profile.objects.all().filter(username=self.request.user).exists()

	def post(self, request, *args, **kwargs):
		hi = self.kwargs['pk']
		comment = Comment.objects.get(pk=hi)
		
		is_liked = False

		if request.user in comment.dislikes.all():
			comment.dislikes.remove(request.user)
			comment.likes.add(request.user)
			is_liked = True
		elif request.user in comment.likes.all():
			comment.likes.remove(request.user)
		else:
			comment.likes.add(request.user)
			is_liked = True

		likes_count = comment.likes.count()
		dislikes_count = comment.dislikes.count()

		return JsonResponse({'likes_count': likes_count, 'liked': is_liked, 'dislikes_count': dislikes_count, 'disliked': False})

class Dislike(LoginRequiredMixin, UserPassesTestMixin, View):
	def get_redirect_url(self):
		return reverse('video-detail', kwargs={'pk': self.object.pk})
	
	def test_func(self):
		return Profile.objects.all().filter(username=self.request.user).exists()
	
	def post(self, request, *args, **kwargs):
		hi = self.kwargs['pk']
		comment = Comment.objects.get(pk=hi)

		is_disliked = False

		if request.user in comment.likes.all():
			comment.likes.remove(request.user)
			comment.dislikes.add(request.user)
			is_disliked = True
		elif request.user in comment.dislikes.all():
			comment.dislikes.remove(request.user)
		else:
			comment.dislikes.add(request.user)
			is_disliked = True

		likes_count = comment.likes.count()
		dislikes_count = comment.dislikes.count()

		return JsonResponse({'likes_count': likes_count, 'liked': False, 'dislikes_count': dislikes_count, 'disliked': is_disliked})