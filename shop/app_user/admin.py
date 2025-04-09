from django.contrib import admin
from django.contrib.auth import get_permission_codename
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from django.utils.safestring import mark_safe

from .models import Profile


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
    'username', 'email', 'first_name', 'last_name', 'is_staff', 'get_location', 'is_verified', 'get_avatar')
    list_select_related = ('profile',)  # добавление profile убирает ненужные запросы к БД
    actions = ('verify_user',)

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

    # @admin.action(
    #     permissions=['verify'],
    #     description='Админка - Верифицировать',
    # )
    def verify_user(self, request, queryset):
        """Верифицировать пользователей"""
        row_update = queryset.count()
        for user in queryset:
            group_verified = Group.objects.get(name='Верифицированный пользователь')
            user.groups.add(group_verified)
            group_simple = Group.objects.get(name='Обычный пользователь')
            if group_simple in user.groups.all():
                user.groups.remove(group_simple)

            profile = Profile.objects.get(user=user)
            profile.is_verified = True
            profile.save(update_fields=['is_verified'])
        if row_update == 1:
            message_bit = "Один пользователь верифицирован"
        else:
            message_bit = f"{row_update} пользователей верифицированы"
        self.message_user(request, f"{message_bit}")

    verify_user.short_description = "Админка - Верифицировать"
    verify_user.allowed_permissions = ['verify']

    def has_verify_permission(self, request):
        # print("Проверка прав")
        opts = self.opts
        # print(opts)
        codename = get_permission_codename('change', opts)
        # print(request.user.has_perm('%s.%s' % (opts.app_label, codename)))
        return request.user.has_perm('%s.%s' % (opts.app_label, codename))


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile)
