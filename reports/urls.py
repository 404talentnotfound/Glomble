from django.contrib import admin
from django.urls import path
from .views import ReportVideo, VideoReportIndex, DetailVideoReport, DeleteVideoReport, ProfileReportIndex, DeleteProfileReport, DetailProfileReport, ReportProfile, BugReportIndex, DeleteBugReport, DetailBugReport, ReportBug, choice_page

urlpatterns = [
    path('', choice_page, name='choice-page'),
    path('videos/index', VideoReportIndex.as_view(), name='video-report-index'),
    path('video/<int:pk>/view', DetailVideoReport.as_view(), name='video-report-detail'),
    path('video/<int:pk>/delete', DeleteVideoReport.as_view(), name='video-report-delete'),
    path('videos/<slug:id>/', ReportVideo.as_view(), name='video-report'),
    path('bug/index', BugReportIndex.as_view(), name='bug-report-index'),
    path('bug/<int:pk>/view', DetailBugReport.as_view(), name='bug-report-detail'),
    path('bug/<int:pk>/delete', DeleteBugReport.as_view(), name='bug-report-delete'),
    path('bug/', ReportBug.as_view(), name='bug-report'),
    path('profiles/index', ProfileReportIndex.as_view(), name='profile-report-index'),
    path('profile/<int:pk>/view', DetailProfileReport.as_view(), name='profile-report-detail'),
    path('profile/<int:pk>/delete', DeleteProfileReport.as_view(), name='profile-report-delete'),
    path('profiles/<slug:id>/', ReportProfile.as_view(), name='profile-report'),
]