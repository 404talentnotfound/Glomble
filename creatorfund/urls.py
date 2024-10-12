from django.urls import path
from .views import CreateFundingProfile, DetailFundingProfile, leave_creator_fund, update_creator_info, CreateFundgroup, DetailFundGroup

urlpatterns = [
    path('join', CreateFundingProfile.as_view(), name='create-funding-profile'),
    path('leave', leave_creator_fund, name='delete-funding-profile'),
    path('edit', update_creator_info, name='edit-funding-profile'),
    path('profile', DetailFundingProfile.as_view(), name='detail-funding-profile'),
    # path('group/create', CreateFundgroup.as_view(), name='create-funding-group'),
    # path('group/<slug:id>', DetailFundGroup.as_view(), name='detail-funding-group'),
]