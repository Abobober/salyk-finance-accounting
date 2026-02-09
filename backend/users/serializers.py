from typing import Any, Dict
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
from rest_framework import serializers


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации нового пользователя.
    Проверяет пароль и создает пользователя.
    """
    password = serializers.CharField(
        write_only=True,  # Пароль только для записи
        required=True,
        validators=[validate_password]  # Встроенные валидаторы Django
    )
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'password2', 'first_name', 'last_name')
        # Можно указать дополнительные настройки для полей, если нужно
    
    def validate(self, attrs):
        """Проверяет, что оба пароля совпадают."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        return attrs
    
    def create(self, validated_data):
        """Создаем нового пользователя."""
        validated_data.pop('password2')  # Убираем password2, т.к. его нет в модели

        # Создаем пользователя с хэшированным паролем
        user = CustomUser.objects.create_user(**validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения и обновления профиля пользователя.
    """
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name', 'telegram_id', 'date_joined')
        read_only_fields = ('id', 'date_joined')  # Эти поля нельзя изменять через API