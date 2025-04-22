from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
from django.forms import model_to_dict, fields_for_model
from django.http import QueryDict

from .models import Profile, SiteUser


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'custom-field__input',
            'placeholder': 'example@mail.com'
        }),
        required=True
    )

    phone_number = forms.CharField(
        label='Номер телефона',
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'custom-field__input',
            'placeholder': '+79991234567'
        }),
        required=False
    )

    address = forms.CharField(
        label='Адрес доставки',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'custom-field__input',
            'placeholder': 'Город, улица, дом, квартира'
        }),
        required=False
    )

    class Meta:
        model = SiteUser
        fields = ('email', 'phone_number', 'address', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Настройка полей паролей
        self.fields['password1'].widget.attrs.update({'class': 'custom-field__input', 'placeholder': ' '})
        self.fields['password2'].widget.attrs.update({'class': 'custom-field__input', 'placeholder': ' '})

        # Изменение labels и help_text
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'
        self.fields['password1'].help_text = 'Минимум 8 символов'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if SiteUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email


    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     for field in iter(self.fields):
    #         self.fields[field].widget.attrs.update({
    #             'class': 'custom-field__input',
    #         })
    #         if field in ("username", "first_name", "last_name", "email", "password1", "password2", ):
    #             self.fields[field].widget.attrs['placeholder'] = ' '
    #         self.fields[field].widget.attrs['data-validate-field'] = field
    #
    #     # self.fields['description'].widget.attrs.update({
    #     #     'class': 'custom-field__input custom-field__input_textarea',
    #     #     'placeholder': ' ',
    #     # })
    #     # self.fields['coordinates'].widget.attrs.update({
    #     #     'class': 'custom-field__input custom-field__input_textarea',
    #     # })


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('birthdate', 'avatar', 'bio',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'custom-field__input',
            })
            if field in ('birthdate', 'avatar', ):
                self.fields[field].widget.attrs['placeholder'] = ' '
            self.fields[field].widget.attrs['data-validate-field'] = field

        self.fields['bio'].widget.attrs.update({
            'class': 'custom-field__input custom-field__input_wide custom-field__input_textarea',
            'placeholder': ' ',
        })


class UserProfileUpdateForm(forms.Form):
    """Форма редактирования профиля Пользователя(User)"""
    first_name = forms.CharField(label='Имя', max_length=50)
    last_name = forms.CharField(label='Фамилия', max_length=50)
    location = forms.CharField(label="Город проживания", max_length=60)
    bio = forms.CharField(label="О себе", max_length=1000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'custom-field__input',
            })
            if field in ('first_name', 'last_name', 'location', ):
                self.fields[field].widget.attrs['placeholder'] = ' '
            self.fields[field].widget.attrs['data-validate-field'] = field

        self.fields['bio'].widget.attrs.update({
            'class': 'custom-field__input custom-field__input_wide custom-field__input_textarea',
            'placeholder': ' ',
        })


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        label='Старый пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'custom-field__input custom-field__input_wide',
            'placeholder': ' ',
        }),
        strip=False,
    )
    new_password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'custom-field__input custom-field__input_wide',
            'placeholder': ' ',
        }),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label='Подтверждение нового пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'custom-field__input custom-field__input_wide',
            'placeholder': ' ',
        }),
        strip=False,
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Неверный старый пароль.')
        return old_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Пароли не совпадают.')
        password_validation.validate_password(password2, self.user)
        return password2

    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user

class FeedbackForm(forms.Form):
    """Форма отправки сообщения"""
    name = forms.CharField(label='Имя', max_length=50)
    email = forms.EmailField(label='электронная почта', )
    message = forms.CharField(label="сообщение", max_length=2000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ('name', 'email', ):
            self.fields[field].widget.attrs.update({
                'class': 'custom-field__input',
                'placeholder': ' '
            })
        self.fields['message'].widget.attrs.update({
            'class': 'custom-field__input custom-field__input_wide custom-field__input_textarea',
            'placeholder': ' ',
        })

