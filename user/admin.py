from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import *


class UserAdmin(BaseUserAdmin):
    list_display = (
        'email',
        'full_name',
        'phone',
        'is_school',
        'is_active',
        'date_joined',

    )
    ordering = ('id',)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                "full_name",
                'login',
                "email",
                       'password1',
                       'password2',
                       ), }),)
    search_fields = ('id','email', 'full_name', 'phone',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info',
         {'fields': (
             'login',
             'is_school',
                "full_name",
                "phone",
                "avatar",
             "subscription_expire"
         )}
         ),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups',)}),)


admin.site.register(User,UserAdmin)

@admin.register(UserToken)
class UserTokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "user_email",
        "user_login",
        "created",
        "short_key",
    )

    list_select_related = ("user",)

    search_fields = (
        "user__email",
        "user__login",
        "user__full_name",
        "key",
    )

    list_filter = (
        "created",
    )

    ordering = ("-created",)

    readonly_fields = ("created", "key")

    def user_email(self, obj):
        return obj.user.email

    def user_login(self, obj):
        return obj.user.login

    def short_key(self, obj):
        return obj.key[:12] + "..."

    user_email.short_description = "Email"
    user_login.short_description = "Login"
    short_key.short_description = "Token"




@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "admin__email",
        "name",
    )


