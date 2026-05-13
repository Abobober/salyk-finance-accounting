# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    search_fields = ('email', 'first_name', 'last_name', 'telegram_id', 'phone')
    
    list_display = ('id', 'email', 'first_name', 'last_name', 'telegram_id', 'is_active', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'telegram_id', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'telegram_id'),
        }),
    )
    
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)