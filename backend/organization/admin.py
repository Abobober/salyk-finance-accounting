"""
Профиль организации: в списке только статус онбординга и e-mail — без ИНН/ФИО в таблице.
Полные реквизиты — на форме объекта (для поддержки при зависшем онбординге).
"""

from django.contrib import admin

from organization.models import OrganizationActivity, OrganizationProfile


class OrganizationActivityInline(admin.TabularInline):
    model = OrganizationActivity
    extra = 0
    raw_id_fields = ('activity',)


@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'onboarding_status', 'org_type', 'tax_regime')
    list_filter = ('onboarding_status', 'org_type', 'tax_regime')
    search_fields = ('user__email',)
    raw_id_fields = ('user',)
    inlines = (OrganizationActivityInline,)

    fieldsets = (
        (None, {'fields': ('user', 'onboarding_status')}),
        ('Настройки', {'fields': ('org_type', 'tax_regime', 'tax_period_type', 'tax_period_preset', 'tax_period_custom_day')}),
        ('Реквизиты (конфиденциально)', {
            'fields': (
                'tin', 'inn', 'taxpayer_name', 'tax_office_code', 'tax_office_name',
                'tax_authority_code', 'tax_authority_name', 'contact_phone',
            ),
        }),
    )

    @admin.display(description='Пользователь')
    def user_email(self, obj):
        return obj.user.email
