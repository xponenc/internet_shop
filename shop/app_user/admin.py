from django.contrib import admin
from django.contrib.auth import get_permission_codename
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from django.utils.safestring import mark_safe

from .models import Profile, SiteUser


class ProfileInline(admin.StackedInline):
    model = Profile
    readonly_fields = ('get_avatar',)

    can_delete = False
    verbose_name = 'Профиль'

    def get_avatar(self, instance):
        if instance.profile.avatar:
            return mark_safe(f'<div><p>{instance.avatar.name}</p>'
                             f'<img src="{instance.avatar.url}" width="100" height="100"/>'
                             f'</div>')

    get_avatar.short_description = 'Аватарка'


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = (
        'email', 'first_name', 'last_name', 'is_staff', 'get_location', 'is_verified', 'get_avatar')
    list_select_related = ('profile',)  # добавление profile убирает ненужные запросы к БД
    actions = ('verify_user',)
    ordering = ['email']  # Изменено с 'username' на 'email'

    def get_inline_instances(self, request, obj=None):
        """Метод переписывается для отображения inline в просмотровом режиме"""
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

    def get_location(self, instance):
        return instance.profile.location

    get_location.short_description = 'Город'

    def get_avatar(self, instance):
        if instance.profile.avatar:
            return mark_safe(f'<img src="{instance.profile.avatar.url}" width="50" height="50">')

    get_avatar.short_description = 'Аватарка'

    def is_verified(self, instance):
        if instance.profile.is_verified:
            return mark_safe(f'<div style="width:10px;height:10px;border-radius:50%;background-color:green;"></div>')
        return mark_safe(f'<div style="width:10px;height:10px;border-radius:50%;background-color:red;"></div>')

    is_verified.short_description = 'Верифицирован'


admin.site.register(SiteUser, CustomUserAdmin)
admin.site.register(Profile)
