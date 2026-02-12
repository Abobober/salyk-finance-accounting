from rest_framework import serializers
from .models import OrganizationProfile, OrganizationActivity


class OrganizationProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для получения и обновления налогового профиля пользователя."""
    class Meta:
        model = OrganizationProfile
        fields = ('org_type', 'tax_regime', 'onboarding_status')
        read_only_fields = ('onboarding_status',)

    def update(self, instance, validated_data):
        if 'org_type' in validated_data and instance.onboarding_status == OrganizationProfile.OnboardingStatus.NOT_STARTED:
            instance.onboarding_status = OrganizationProfile.OnboardingStatus.ORG_TYPE
        elif 'tax_regime' in validated_data and instance.onboarding_status in [OrganizationProfile.OnboardingStatus.ORG_TYPE]:
            instance.onboarding_status = OrganizationProfile.OnboardingStatus.TAX_REGIME
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
