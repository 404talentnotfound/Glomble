"""Glomble URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from videos import views as video_views
from django.conf import settings
from django.conf.urls.static import static
from profiles import views as user_views
from django.contrib.auth import views as auth_views
from profiles.views import CustomPasswordResetView

handler404 = 'videos.views.handler500'

urlpatterns = [
    path('eb16f4a593b6fccbc1c8c92a53e2152ce738d9de251f8d60fdbb88789390e17a/', admin.site.urls),
    path('accounts/profile/', video_views.redirect_index),
    path('', video_views.Index.as_view(), name='index'),
    path('mcdonalds', video_views.mcdonalds),
    path('videos/', include('videos.urls')),
    path('notifications/', include('notifications.urls')),
    path('profiles/', include('profiles.urls')),
    path('comments/', include('comments.urls', namespace='comments')),
    path("register/", user_views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="profiles/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(template_name="profiles/logout.html"), name="logout"),
    path("profile/", user_views.profile, name="profile-page"),
    path('report/', include('reports.urls')),
    path('creatorfund/', include('creatorfund.urls')),

    path("password-reset/", CustomPasswordResetView.as_view(
        template_name="profiles/password_reset.html",
        email_template_name="profiles/password_reset_email.html"),
        name="password_reset"),

    path("password-reset/done", auth_views.PasswordResetDoneView.as_view(
        template_name="profiles/password_reset_done.html"), name="password_reset_done"),

    path("password-reset-confirm/<uidb64>/<token>", auth_views.PasswordResetConfirmView.as_view(
        template_name="profiles/password_reset_confirm.html"), name="password_reset_confirm"),

    path("password-reset-complete", auth_views.PasswordResetCompleteView.as_view(
        template_name="profiles/password_reset_complete.html"), name="password_reset_complete"),
        
    path('activate/<uidb64>/<token>', user_views.activate, name='activate')


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
