from django.shortcuts import reverse, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import DeleteView, UpdateView
from django.http import JsonResponse
from videos.models import Comment
from notifications.models import BaseNotification

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
	
	def test_func(self):
		comment = self.get_object()
		return self.request.user == comment.commenter.username or self.request.user.is_superuser

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

class AddLike(LoginRequiredMixin, View):
	def get_redirect_url(self):
		return reverse('video-detail', kwargs={'pk': self.object.post.id})

	def post(self, request, *args, **kwargs):
		hi = self.kwargs['pk']
		comment = Comment.objects.get(pk=hi)
		
		is_dislike = False

		if request.user in comment.dislikes.all():
			is_dislike = True

		if is_dislike:
			comment.dislikes.remove(request.user)

		is_like = False

		if request.user in comment.likes.all():
			is_like = True

		if not is_like:
			comment.likes.add(request.user)

		if is_like:
			comment.likes.remove(request.user)

		likes_count = comment.likes.count()

		dislikes_count = comment.dislikes.count()

		return JsonResponse({'likes_count': likes_count, 'liked': is_like, 'dislikes_count': dislikes_count, 'disliked': is_dislike})

class Dislike(LoginRequiredMixin, View):
	def get_redirect_url(self):
		return reverse('video-detail', kwargs={'pk': self.object.pk})
	def post(self, request, *args, **kwargs):
		hi = self.kwargs['pk']
		comment = Comment.objects.get(pk=hi)

		is_like = False

		if request.user in comment.likes.all():
			is_like = True

		if is_like:
			comment.likes.remove(request.user)

		is_dislike = False

		if request.user in comment.dislikes.all():
			is_dislike = True

		if not is_dislike:
			comment.dislikes.add(request.user)

		if is_dislike:
			comment.dislikes.remove(request.user)

		likes_count = comment.likes.count()

		dislikes_count = comment.dislikes.count()

		return JsonResponse({'likes_count': likes_count, 'liked': is_like, 'dislikes_count': dislikes_count, 'disliked': is_dislike})