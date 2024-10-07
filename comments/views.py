from django.shortcuts import render, reverse, redirect
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import DeleteView, UpdateView
from django.http import JsonResponse
from videos.models import Comment, Video
from profiles.models import Profile
from videos.forms import CommentForm

class DeleteComment(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = Comment
	template_name = 'videos/comment_delete.html'

	def get_redirect_url(self):
		return reverse('video-detail', kwargs={'id': self.object.post.id})


	def get_success_url(self):
		return reverse('video-detail', kwargs={'id': self.object.post.id})
	
	def test_func(self):
		comment = self.get_object()
		return self.request.user == comment.commenter or self.request.user.is_superuser

class AddLike(LoginRequiredMixin, View):
	def get_redirect_url(self):
		return reverse('video-detail', kwargs={'pk': self.object.post.pk})

	def post(self, request, *args, **kwargs):
		hi = self.kwargs['pk']
		video = Comment.objects.get(pk=hi)
		
		is_dislike = False

		for dislike in video.dislikes.all():
			if dislike == request.user:
				is_dislike = True
				break

		if is_dislike:
			video.dislikes.remove(request.user)

		is_like = False

		for like in video.likes.all():
			if like == request.user:
				is_like = True
				break

		if not is_like:
			video.likes.add(request.user)

		if is_like:
			video.likes.remove(request.user)

		likes_count = video.likes.count()

		dislikes_count = video.dislikes.count()

		return JsonResponse({'likes_count': likes_count, 'liked': is_like, 'dislikes_count': dislikes_count, 'disliked': is_dislike})

class Dislike(LoginRequiredMixin, View):
	def get_redirect_url(self):
		return reverse('video-detail', kwargs={'pk': self.object.pk})
	def post(self, request, *args, **kwargs):
		hi = self.kwargs['pk']
		video = Comment.objects.get(pk=hi)

		is_like = False

		for like in video.likes.all():
			if like == request.user:
				is_like = True
				break

		if is_like:
			video.likes.remove(request.user)

		is_dislike = False

		for dislike in video.dislikes.all():
			if dislike == request.user:
				is_dislike = True
				break

		if not is_dislike:
			video.dislikes.add(request.user)

		if is_dislike:
			video.dislikes.remove(request.user)

		likes_count = video.likes.count()

		dislikes_count = video.dislikes.count()

		return JsonResponse({'likes_count': likes_count, 'liked': is_like, 'dislikes_count': dislikes_count, 'disliked': is_dislike})