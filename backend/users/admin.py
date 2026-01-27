from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    """Настройки отображения модели CustomUser в админке."""
    # Какие поля отображать в списке пользователей
    list_display = ('email', 'first_name', 'last_name', 'telegram_id', 'is_staff')
    
    # По каким полям можно фильтровать
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    
    # Поля при редактировании пользователя в админке
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'telegram_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Поля при создании пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'telegram_id'),
        }),
    )

    ordering = ('email',)

# Регистрируем нашу модель с кастомной админкой
admin.site.register(CustomUser, CustomUserAdmin)
