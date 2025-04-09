import io

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView, LogoutView
from django.core.files.base import ContentFile, File
from django.core.files.images import get_image_dimensions
from django.db.models import Count
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views import View, generic
from PIL import Image

from .forms import UserRegistrationForm, UserProfileForm, UserProfileUpdateForm, FeedbackForm
from .models import Profile


class UserLogin(LoginView):
    """Авторизация пользователя"""
    template_name = "app_users/login.html"


class UserLogout(LogoutView):
    """Выход пользователя из системы"""
    template_name = "app_users/logout.html"


class UserRegistration(View):
    """Регистрация пользователя"""

    @classmethod
    def get(cls, request):
        user_form = UserRegistrationForm()
        profile_form = UserProfileForm()
        context = {
            'forms': [user_form, profile_form]
        }
        return render(request, 'app_users/registration.html', context=context)

    @classmethod
    def post(cls, request):
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            try:
                default_group = Group.objects.get(name='Обычный пользователь')
            except Group.DoesNotExist:
                user_form.add_error('username', 'Ошибка базы -  группы Обычный пользователь не существует')
                forms = [user_form, profile_form]
                return render(request, 'app_users/registration.html', {'forms': forms})
            if default_group:
                user.groups.add(default_group)
            profile = profile_form.save(commit=False)
            profile.user = user
            image = profile_form.cleaned_data.get('avatar')
            if image:
                file = avatar_resize(image)
                profile.avatar.save(file.name, file)
            profile.save()

            username = user_form.cleaned_data.get('username')
            password = user_form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, 'Ваш аккаунт успешно создан. Добро пожаловать.')
            return redirect(reverse_lazy('app_users:profile', kwargs={'pk': user.id}))
        forms = [user_form, profile_form]
        return render(request, 'app_users/registration.html', {'forms': forms})


def avatar_resize(image):
    """Изменение размеров файла аватара"""
    img_width, img_height = get_image_dimensions(image)
    image_data = Image.open(image)

    if img_height > 100:  # Уменьшаем размер, если высота больше 100px
        new_img_height = 100
        new_img_width = int(new_img_height * img_width / img_height)
        image_data = image_data.resize((new_img_width, new_img_height), Image.LANCZOS)

    output = io.BytesIO()
    image_data.save(output, format="JPEG", optimize=True, quality=75)
    output.seek(0)

    content_file = ContentFile(output.read())  # Создаём файл в памяти
    output.close()

    return File(content_file)


class UserProfileView(generic.DetailView):
    """Просмотр профиля пользователя"""
    model = User
    template_name = "app_users/profile.html"
    queryset = User.objects.select_related("profile").all().annotate(total_posts=Count("blog__post"))


class UserProfileUpdateView(UserPassesTestMixin, View):
    """Редактирование профиля пользователя"""
    # permission_required = 'app_users.change_profile'
    # model = Profile
    # form_class = UserProfileUpdateForm
    # template_name = "users/profile_update.html"

    def test_func(self):
        user = Profile.objects.get(id=self.kwargs.get("pk")).user
        check_status = (self.request.user == user) or \
                       (self.request.user.groups.filter(name__in=['Модератор']).exists())
        return check_status

    @classmethod
    def get(cls, request, *args, **kwargs):
        profile_id = kwargs.get('pk')
        profile = Profile.objects.get(id=profile_id)
        # form = UserProfileUpdateForm(instance=profile)
        form = UserProfileUpdateForm(initial={
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'location': profile.location,
            'bio': profile.bio,
        })
        return render(request, 'app_users/profile_update.html', {'form': form, 'profile': profile})

    def post(self, request, *args, **kwargs):
        profile_id = kwargs.get('pk')
        profile = Profile.objects.get(id=profile_id)
        form = UserProfileUpdateForm(request.POST)
        if form.is_valid():
            if form.has_changed():
                profile.location = form.cleaned_data.get('location')
                profile.bio = form.cleaned_data.get('bio')
                profile.user.first_name = form.cleaned_data.get('first_name')
                profile.user.last_name = form.cleaned_data.get('last_name')
                profile.save(update_fields=['location', 'bio'])
                profile.user.save(update_fields=['first_name', 'last_name'])
            return redirect(profile.get_absolute_url())
        return render(request, 'app_users/profile_update.html', {'form': form})


class UserListView(generic.ListView):
    """Списковый просмотр пользователей"""
    model = User
    template_name = "app_users/user_list.html"
    queryset = User.objects.select_related("profile").all()


class UserVerifyView(PermissionRequiredMixin, View):
    """Представление перевода пользователя в группу Верифицированные пользователи"""
    # @permission_required('app_users.verify')
    permission_required = 'app_users.verify'

    @classmethod
    def get(cls, request, pk, *args, **kwargs):
        user = User.objects.get(id=pk)
        user_group = Group.objects.get(name='Верифицированный пользователь')
        # user.groups.add(user_group)
        user.groups.set([user_group])

        profile = Profile.objects.get(user=user)
        profile.is_verified = True
        profile.save(update_fields=['is_verified'])

        messages.success(request, f'Пользователь {user.get_full_name()} успешно верифицирован')

        return HttpResponseRedirect(reverse('app_users:user_list'))


class UserFeedbackView(View):
    """Отправка сообщения обратной связи"""

    def get(self, *args, **kwargs):
        if self.request.user.is_anonymous:
            feedback_form = FeedbackForm()
        else:
            feedback_form = FeedbackForm(initial={
                "name": f"{self.request.user.first_name} {self.request.user.last_name}",
                "email": self.request.user.email
            })
        return render(request=self.request, template_name="app_users/feedback.html", context={"form": feedback_form})


    def post(self, *args, **kwargs):
        is_ajax = self.request.headers.get('x-requested-with') == 'XMLHttpRequest'
        feedback_form = FeedbackForm(self.request.POST)
        if feedback_form.is_valid():
            print(feedback_form.cleaned_data)
            # Обработка формы
            if is_ajax:
                return JsonResponse(
                    {
                        "message": "Сообщение успешно отправлено",
                        "redirect_url": reverse_lazy("index"),
                     }, status=200)
            return redirect("index")
        if is_ajax:
            csrf_token = get_token(self.request)
            return JsonResponse(
                {
                    "form_html": render_to_string(
                        template_name="widgets/_custom-form.html",
                        context={"form": feedback_form}),
                    "csrf_token": csrf_token,
                },
                status=400)
        return render(request=self.request, template_name="app_users/feedback.html", context={"form": feedback_form})


class CheckEmailExistView(View):
    """Представление проверки e-mail для регистрации"""

    def get(self, *args, **kwargs):
        is_ajax = self.request.headers.get('x-requested-with') == 'XMLHttpRequest'
        print(args, kwargs, self.request.GET)
        email = self.request.GET.get("email")
        if is_ajax and email:
            # try:
            email_exist = User.objects.filter(email=email).exists()
            if email_exist:
                return JsonResponse({"available": False}, status=200)
            return JsonResponse({"available": True},status=200)
            # except Exception:
            #     return JsonResponse({}, status=500)
        return HttpResponse(status=404)