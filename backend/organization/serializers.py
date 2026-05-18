from django.db import transaction
from rest_framework import serializers

from .models import OrganizationActivity, OrganizationProfile
from .services import get_or_create_organization_profile


class OrganizationProfileSerializer(serializers.ModelSerializer):
    tax_period_type_display = serializers.CharField(source='get_tax_period_type_display', read_only=True)
    tax_period_preset_display = serializers.CharField(source='get_tax_period_preset_display', read_only=True)
    text_fields_to_normalize = (
        'tin',
        'inn',
        'taxpayer_name',
        'tax_office_code',
        'tax_office_name',
        'tax_authority_code',
        'tax_authority_name',
        'contact_phone',
    )

    class Meta:
        model = OrganizationProfile
        fields = (
            'org_type', 'tax_regime', 'onboarding_status',
            'tin', 'inn', 'taxpayer_name',
            'tax_office_code', 'tax_office_name',
            'tax_authority_code', 'tax_authority_name',
            'contact_phone',
            'tax_period_type', 'tax_period_type_display',
            'tax_period_preset', 'tax_period_preset_display',
            'tax_period_custom_day',
        )
        read_only_fields = ('onboarding_status', 'tax_period_type_display', 'tax_period_preset_display')

    def _normalize_text_field(self, attrs, field_name):
        if field_name not in attrs:
            return

        value = attrs[field_name]
        if value is None:
            return

        normalized_value = value.strip()
        if not normalized_value:
            raise serializers.ValidationError({
                field_name: 'This field may not be blank.',
            })

        attrs[field_name] = normalized_value

    def validate(self, attrs):
        instance = self.instance
        tax_period_type = attrs['tax_period_type'] if 'tax_period_type' in attrs else (instance.tax_period_type if instance else None)
        tax_period_preset = attrs['tax_period_preset'] if 'tax_period_preset' in attrs else (instance.tax_period_preset if instance else None)
        tax_period_custom_day = attrs['tax_period_custom_day'] if 'tax_period_custom_day' in attrs else (instance.tax_period_custom_day if instance else None)

        for field_name in self.text_fields_to_normalize:
            self._normalize_text_field(attrs, field_name)

        if tax_period_type == OrganizationProfile.TaxPeriodType.CUSTOM:
            tax_period_preset = None

        if tax_period_type == OrganizationProfile.TaxPeriodType.PRESET and not tax_period_preset:
            raise serializers.ValidationError({
                'tax_period_preset': 'Preset tax period is required.',
            })

        if tax_period_type == OrganizationProfile.TaxPeriodType.PRESET and tax_period_custom_day is not None:
            if tax_period_custom_day < 1 or tax_period_custom_day > 31:
                raise serializers.ValidationError({
                    'tax_period_custom_day': 'Start day must be between 1 and 31.',
                })

        if tax_period_type == OrganizationProfile.TaxPeriodType.CUSTOM:
            if not tax_period_custom_day:
                raise serializers.ValidationError({
                    'tax_period_custom_day': 'Custom day is required for custom periods.',
                })
            if tax_period_custom_day < 1 or tax_period_custom_day > 31:
                raise serializers.ValidationError({
                    'tax_period_custom_day': 'Custom day must be between 1 and 31.',
                })

        return attrs

    def update(self, instance, validated_data):
        if 'org_type' in validated_data and instance.onboarding_status == OrganizationProfile.OnboardingStatus.NOT_STARTED:
            instance.onboarding_status = OrganizationProfile.OnboardingStatus.ORG_TYPE
        elif 'tax_regime' in validated_data and instance.onboarding_status in [OrganizationProfile.OnboardingStatus.ORG_TYPE]:
            instance.onboarding_status = OrganizationProfile.OnboardingStatus.TAX_REGIME

        if validated_data.get('tax_period_type') == OrganizationProfile.TaxPeriodType.CUSTOM:
            validated_data['tax_period_preset'] = None

        return super().update(instance, validated_data)


class OnboardingFinalizeSerializer(serializers.ModelSerializer):
    """
    Завершение онбординга: те же поля, что собирает SPA (ИНН, налоговый орган и т.д.).
    Поля tin / tax_office_* — необязательны; при пустом tin копируем ИНН для совместимости со старым кодом отчётов.
    """

    class Meta:
        model = OrganizationProfile
        fields = ()

    def validate(self, attrs):
        profile = self.instance
        if not profile.org_type:
            raise serializers.ValidationError('Organization type is required.')
        if not profile.tax_regime:
            raise serializers.ValidationError('Tax regime is required.')
        if not profile.tax_period_type:
            raise serializers.ValidationError('Tax period is required.')

        if not (profile.inn or '').strip():
            raise serializers.ValidationError('INN is required.')
        if not (profile.taxpayer_name or '').strip():
            raise serializers.ValidationError('Taxpayer name is required.')
        if not (profile.tax_authority_code or '').strip():
            raise serializers.ValidationError('Tax authority code is required.')
        if not (profile.tax_authority_name or '').strip():
            raise serializers.ValidationError('Tax authority name is required.')
        if not (profile.contact_phone or '').strip():
            raise serializers.ValidationError('Contact phone is required.')

        if not profile.activities.exists():
            raise serializers.ValidationError('At least one activity is required.')
        if not profile.activities.filter(is_primary=True).exists():
            raise serializers.ValidationError('Primary activity is required.')
        return attrs

    def update(self, instance, validated_data):
        inn = (instance.inn or '').strip()
        if inn and not (instance.tin or '').strip():
            instance.tin = inn
        instance.onboarding_status = OrganizationProfile.OnboardingStatus.COMPLETED
        instance.save()
        return instance


class OrganizationActivitySerializer(serializers.ModelSerializer):
    activity_name = serializers.CharField(source='activity.name', read_only=True)

    class Meta:
        model = OrganizationActivity
        fields = ('id', 'activity', 'activity_name', 'cash_tax_rate', 'non_cash_tax_rate', 'is_primary')
        read_only_fields = ('id', 'activity_name')

    def validate(self, attrs):
        profile = get_or_create_organization_profile(self.context['request'].user)
        current_pk = getattr(self.instance, 'pk', None)
        if attrs.get('activity') and profile.activities.exclude(pk=current_pk).filter(activity=attrs['activity']).exists():
            raise serializers.ValidationError({'activity': 'This activity is already linked to the organization.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        profile = validated_data['profile']
        if validated_data.get('is_primary'):
            profile.activities.filter(is_primary=True).update(is_primary=False)
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        if validated_data.get('is_primary'):
            instance.profile.activities.exclude(pk=instance.pk).filter(is_primary=True).update(is_primary=False)
        return super().update(instance, validated_data)


class OrganizationStatusSerializer(serializers.Serializer):
    onboarding_status = serializers.CharField()
    is_completed = serializers.BooleanField()


class TaxPeriodCurrentPeriodSerializer(serializers.Serializer):
    start = serializers.CharField()
    end = serializers.CharField()


class TaxPeriodResponseSerializer(serializers.Serializer):
    tax_period_type = serializers.CharField()
    tax_period_preset = serializers.CharField(allow_null=True)
    tax_period_custom_day = serializers.IntegerField(allow_null=True)
    current_period = TaxPeriodCurrentPeriodSerializer()
    next_period_start = serializers.CharField()
