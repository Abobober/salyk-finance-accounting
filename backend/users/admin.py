from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    """Настройки отображения модели CustomUser в админке."""
    # Какие поля отображать в списке пользователей
    list_display = ('username', 'email', 'first_name', 'last_name', 'telegram_id', 'is_staff')
    
    # По каким полям можно фильтровать
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    
    # Поля при редактировании пользователя в админке
    fieldsets = UserAdmin.fieldsets + (
        ('Telegram', {'fields': ('telegram_id',)}),  # Добавляем  поле в конец формы
    )
    
    # Поля при создании пользователя
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Telegram', {'fields': ('telegram_id',)}),
    )

# Регистрируем нашу модель с кастомной админкой
admin.site.register(CustomUser, CustomUserAdmin)
