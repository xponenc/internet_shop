from django.urls import path

from .views import UserLogin, UserLogout, UserRegistration, UserProfileView, UserListView, \
    UserProfileUpdateView, CheckEmailExistView, UserFeedbackView, UserVerifyView

app_name = 'app_users'

urlpatterns = [
    path('login/', UserLogin.as_view(), name='login'),
    path('logout/', UserLogout.as_view(), name='logout'),
    path('sign-up/', UserRegistration.as_view(), name='sign-up'),

    path('<int:pk>/profile/', UserProfileView.as_view(), name='profile'),
    path('<int:pk>/profile/update/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('list/', UserListView.as_view(), name='users'),
    path('<int:pk>/verify/', UserVerifyView.as_view(), name='verify'),
    path('feedback/', UserFeedbackView.as_view(), name='feedback'),
    path('check_email/', CheckEmailExistView.as_view(), name='check-email'),

]
