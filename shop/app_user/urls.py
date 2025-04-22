from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, \
    PasswordResetView
from django.urls import path, reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

from .views import UserLogin, UserLogout, UserRegistration, UserListView, \
    UserProfileUpdateView, CheckEmailExistView, UserFeedbackView, UserVerifyView, UserDetailView, UserActivateView, \
    delete_account, delete_account_confirm, change_password

app_name = 'app_user'

urlpatterns = [
    path('login/', UserLogin.as_view(), name='login'),
    path('logout/', UserLogout.as_view(), name='logout'),
    path('sigh-in/', UserRegistration.as_view(), name='sigh-in'),
    # Активация аккаунта (GET запрос)
    path('activate/<uidb64>/<token>/', UserActivateView.as_view(), name='activate'),

    # Страница подтверждения отправки email
    path('email-confirmation-sent/', TemplateView.as_view(
        template_name='app_user/email_confirmation_sent.html'
    ), name='email_confirmation_sent'),
    path('password_reset/', PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        success_url=reverse_lazy('app_user:password_reset_done')
    ), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url=reverse_lazy('app_user:password_reset_complete')
    ), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    path('users/<int:pk>/profile/', UserDetailView.as_view(), name='profile'),
    path('users/<int:pk>/profile/update/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('users/', UserListView.as_view(), name='users'),
    path('users/<int:pk>/verify/', UserVerifyView.as_view(), name='verify'),
    path('users/feedback/', UserFeedbackView.as_view(), name='feedback'),
    path('users/check_email/', CheckEmailExistView.as_view(), name='check-email'),
    path('delete-account/', delete_account, name='delete_account'),
    path('delete-account/confirm/<uidb64>/<token>/', delete_account_confirm, name='delete_account_confirm'),
    path('delete-account/email-sent/', TemplateView.as_view(template_name="registration/delete_account_email_sent.html"),
         name='delete_account_email_sent'),
    path('change-password/', change_password, name='change_password'),

]
