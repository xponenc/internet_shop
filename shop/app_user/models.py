import datetime
import os
from time import timezone

from django.contrib.auth.models import User, AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse


class CustomUserManager(UserManager):
    def get_by_natural_key(self, email):
        """Логин по email"""
        return self.get(email__iexact=email)


class SiteUser(AbstractUser):
    """Модель пользователя на сайте"""
    username = None  # <-- полностью отключаем это поле
    email = models.EmailField(unique=True, verbose_name='Email')
    phone_regex = RegexValidator(regex=r'^((\+7)+([0-9]){10})$',
                                 message="Телефонный номер должен быть введен в формате: '+79991234567'.")
    phone_number = models.CharField(verbose_name="Телефон", validators=[phone_regex, ], max_length=12, unique=True)
    address = models.CharField(verbose_name="Адрес доставки", max_length=60)
    registered_at = models.DateTimeField(verbose_name="Дата регистрации", auto_now_add=True)
    verified_at = models.DateTimeField(verbose_name="Дата верификации", null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def get_absolute_url(self):
        return reverse('app_user:user', args=[str(self.user.id)])

    def __str__(self):
        return self.email


class Profile(models.Model):
    """Модель Профиль пользователя, расширяющая модель SiteUser через связь OnrToOne"""

    def create_path(self, filename):
        if self.user.first_name and self.user.last_name:
            user = '_'.join([self.user.first_name, self.user.last_name, 'avatar'])
        else:
            user = '_' + self.user.email.split('@')[0]
        return os.path.sep.join(['users', f'user-id-{self.user.id}', 'avatars', user + ".jpg"])

    def validate_date_in_past(value):
        today = datetime.date.today()
        if value >= today:
            raise ValidationError('Дата рождения должна быть меньше текущей даты')

    user = models.OneToOneField(SiteUser, on_delete=models.CASCADE)
    birthdate = models.DateField(verbose_name="Дата рождения", validators=[validate_date_in_past])
    bio = models.TextField(verbose_name="О себе", max_length=1000, blank=True, null=True)
    avatar = models.ImageField(verbose_name="Аватар пользователя", upload_to=create_path, blank=True)

    objects = models.Manager()

    def __str__(self):
        return f"{self.user.username}"






