from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
from django.forms import model_to_dict, fields_for_model
from django.http import QueryDict

from .models import Profile


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(label='Имя', max_length=50, help_text='Имя')
    last_name = forms.CharField(label='Фамилия', max_length=50)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'custom-field__input',
            })
            if field in ("username", "first_name", "last_name", "email", "password1", "password2", ):
                self.fields[field].widget.attrs['placeholder'] = ' '
            self.fields[field].widget.attrs['data-validate-field'] = field

        # self.fields['description'].widget.attrs.update({
        #     'class': 'custom-field__input custom-field__input_textarea',
        #     'placeholder': ' ',
        # })
        # self.fields['coordinates'].widget.attrs.update({
        #     'class': 'custom-field__input custom-field__input_textarea',
        # })


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('birthdate', 'phone', 'location', 'avatar', 'bio',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'custom-field__input',
            })
            if field in ('birthdate', 'phone', 'location', 'avatar', ):
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