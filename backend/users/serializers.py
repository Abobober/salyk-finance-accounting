from typing import Any, Dict

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import ActivityCode, CustomUser, OrganizationProfile


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


class OnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationProfile
        fields = ('org_type', 'tax_regime', 'primary_activity', 
                  'additional_activities', 'cash_tax_rate', 'non_cash_tax_rate')

    def validate_tax_regime(self, value):
        if value == OrganizationProfile.TaxRegime.GENERAL:
            raise serializers.ValidationError("Общий налоговый режим временно недоступен.")
        return value
    
class ActivityCodeSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения справочника видов деятельности."""
    class Meta:
        model = ActivityCode
        fields = ('code', 'section', 'name')
        read_only_fields = ('code', 'section', 'name')

class OrganizationProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для онбординга и управления профилем налогоплательщика."""
    
    # Добавляем read-only поля названий для удобства
    primary_activity_name = serializers.CharField(source='primary_activity.name', read_only=True)

    class Meta:
        model = OrganizationProfile
        fields = (
            'org_type', 
            'tax_regime', 
            'primary_activity', 
            'primary_activity_name',
            'additional_activities', 
            'cash_tax_rate', 
            'non_cash_tax_rate',
            'is_onboarded', # это поле для определения статуса онбординга
        )
        # is_onboarded будем менять программно при сохранении
        read_only_fields = ('is_onboarded', 'primary_activity_name') 

    def validate_tax_regime(self, value):
        """Валидация заглушки для Общего налогового режима."""
        if value == OrganizationProfile.TaxRegime.GENERAL:
            raise serializers.ValidationError("Общий налоговый режим временно недоступен для выбора.")
        return value

    def update(self, instance, validated_data):
        """При обновлении профиля автоматически помечаем онбординг как завершенный."""
        updated_instance = super().update(instance, validated_data)
        if not updated_instance.is_onboarded:
            updated_instance.is_onboarded = True
            updated_instance.save()
        return updated_instance