from rest_framework import serializers
from .models import OrganizationProfile, OrganizationActivity


class OrganizationProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для получения и обновления налогового профиля пользователя."""
    
    tax_period_type_display = serializers.CharField(source='get_tax_period_type_display', read_only=True)
    tax_period_preset_display = serializers.CharField(source='get_tax_period_preset_display', read_only=True)
    
    class Meta:
        model = OrganizationProfile
        fields = (
            'org_type', 'tax_regime', 'onboarding_status',
            'tax_period_type', 'tax_period_type_display',
            'tax_period_preset', 'tax_period_preset_display',
            'tax_period_custom_day'
        )
        read_only_fields = ('onboarding_status', 'tax_period_type_display', 'tax_period_preset_display')

    def validate(self, attrs):
        """Validate tax period settings."""
        tax_period_type = attrs.get('tax_period_type') or self.instance.tax_period_type if self.instance else None
        tax_period_preset = attrs.get('tax_period_preset') or (self.instance.tax_period_preset if self.instance else None)
        tax_period_custom_day = attrs.get('tax_period_custom_day') or (self.instance.tax_period_custom_day if self.instance else None)
        
        if tax_period_type == OrganizationProfile.TaxPeriodType.PRESET:
            if not tax_period_preset:
                raise serializers.ValidationError({
                    'tax_period_preset': 'Необходимо выбрать предустановленный период.'
                })
            if tax_period_custom_day is not None:
                raise serializers.ValidationError({
                    'tax_period_custom_day': 'День месяца не используется для предустановленного периода.'
                })
        elif tax_period_type == OrganizationProfile.TaxPeriodType.CUSTOM:
            if not tax_period_custom_day:
                raise serializers.ValidationError({
                    'tax_period_custom_day': 'Необходимо указать день месяца для пользовательского периода (1-31).'
                })
            if tax_period_custom_day < 1 or tax_period_custom_day > 31:
                raise serializers.ValidationError({
                    'tax_period_custom_day': 'День месяца должен быть от 1 до 31.'
                })
            if tax_period_preset is not None:
                raise serializers.ValidationError({
                    'tax_period_preset': 'Предустановленный период не используется для пользовательского типа.'
                })
        
        return attrs

    def update(self, instance, validated_data):
        if 'org_type' in validated_data and instance.onboarding_status == OrganizationProfile.OnboardingStatus.NOT_STARTED:
            instance.onboarding_status = OrganizationProfile.OnboardingStatus.ORG_TYPE
        elif 'tax_regime' in validated_data and instance.onboarding_status in [OrganizationProfile.OnboardingStatus.ORG_TYPE]:
            instance.onboarding_status = OrganizationProfile.OnboardingStatus.TAX_REGIME
        
        # Clear unused tax period fields
        if validated_data.get('tax_period_type') == OrganizationProfile.TaxPeriodType.PRESET:
            validated_data['tax_period_custom_day'] = None
        elif validated_data.get('tax_period_type') == OrganizationProfile.TaxPeriodType.CUSTOM:
            validated_data['tax_period_preset'] = None
        
        return super().update(instance, validated_data)


class OnboardingFinalizeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для финализации онбординга.
    """
    class Meta:
        model = OrganizationProfile
        fields = ()

    def validate(self, attrs):
        profile = self.instance
        if not profile.org_type:
            raise serializers.ValidationError("Не выбран тип организации")
        if not profile.tax_regime:
            raise serializers.ValidationError("Не выбран налоговый режим")
        if not profile.activities.exists():
            raise serializers.ValidationError("Не добавлено ни одного вида деятельности")
        if not profile.activities.filter(is_primary=True).exists():
            raise serializers.ValidationError("Не выбран основной вид деятельности")
        return attrs

    def update(self, instance, validated_data):
        instance.onboarding_status = OrganizationProfile.OnboardingStatus.COMPLETED
        instance.save()
        return instance



class OrganizationActivitySerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления видов деятельности в профиль пользователя.
    """
    activity_name = serializers.CharField(source='activity.name', read_only=True)

    class Meta:
        model = OrganizationActivity
        fields = ('id', 'activity', 'activity_name', 'cash_tax_rate', 'non_cash_tax_rate', 'is_primary')
        read_only_fields = ('id', 'activity_name')

    def validate(self, attrs):
        profile = self.context['request'].user.organization
        if attrs.get('is_primary') and profile.activities.filter(is_primary=True).exists():
            raise serializers.ValidationError("Основной вид деятельности уже выбран")
        return attrs

class OrganizationStatusSerializer(serializers.Serializer):
    onboarding_status = serializers.CharField()
    is_completed = serializers.BooleanField()


class TaxPeriodCurrentPeriodSerializer(serializers.Serializer):
    start = serializers.CharField()
    end = serializers.CharField()


class TaxPeriodResponseSerializer(serializers.Serializer):
    """Response for GET /api/organization/tax-period/"""

    tax_period_type = serializers.CharField()
    tax_period_preset = serializers.CharField(allow_null=True)
    tax_period_custom_day = serializers.IntegerField(allow_null=True)
    current_period = TaxPeriodCurrentPeriodSerializer()
    next_period_start = serializers.CharField()
