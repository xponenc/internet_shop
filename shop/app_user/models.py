import datetime
import os
from time import timezone

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse


class Profile(models.Model):
    """Модель Профиль пользователя, расширяющая модель User через связь OnrToOne"""

    def create_path(self, filename):
        if self.user.first_name and self.user.last_name:
            user = '_'.join([self.user.first_name, self.user.last_name, 'avatar'])
        else:
            user = '_' + self.user.username + 'avatar'
        return os.path.sep.join(['users',
                                 f'user-id-{self.user.id}',
                                 'avatars',
                                user + ".jpg"])

    def validate_date_in_past(value):
        today = datetime.date.today()
        if value >= today:
            raise ValidationError('Дата рождения должна быть меньше текущей даты')

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    max_blogs = models.IntegerField(verbose_name="Максимальное количество возможных блогов", default=3)
    birthdate = models.DateField(verbose_name="Дата рождения", validators=[validate_date_in_past])
    phone_regex = RegexValidator(regex=r'^((\+7)+([0-9]){10})$',
                                 message="Телефонный номер должен быть введен в формате: '+79991234567'.")
    phone = models.CharField(verbose_name="Телефон", validators=[phone_regex, ], max_length=12, unique=True)
    location = models.CharField(verbose_name="Город проживания", max_length=60)
    bio = models.TextField(verbose_name="О себе", max_length=1000, blank=True, null=True)
    avatar = models.ImageField(verbose_name="Аватар пользователя", upload_to=create_path, blank=True)
    is_verified = models.BooleanField(verbose_name="Пользователь верифицирован", default=False)
    created_at = models.DateTimeField(verbose_name="Дата регистрации", auto_now_add=True)

    objects = models.Manager()

    class Meta:
        permissions = (
            ("verify", "Верифицировать"),
        )

    def __str__(self):
        return f"{self.user.username}"

    def get_absolute_url(self):
        return reverse('app_users:profile', args=[str(self.user.id)])

