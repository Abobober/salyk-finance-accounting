from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import csv

from finance.models import Category, Transaction, TransactionLog
from finance.services.transaction_service import TransactionService
from organization.models import OrganizationActivity


class TransactionDeletedFilter(admin.SimpleListFilter):
    title = 'корзина'
    parameter_name = 'trash'
    def lookups(self, request, model_admin):
        return (('active', 'Только активные'), ('deleted', 'Только удалённые'))
    def queryset(self, request, queryset):
        if self.value() == 'deleted':
            return queryset.filter(deleted_at__isnull=False)
        if self.value() == 'active':
            return queryset.filter(deleted_at__isnull=True)
        return queryset


# Кастомный фильтр по сумме (диапазон)
class AmountRangeFilter(admin.SimpleListFilter):
    title = 'сумма (диапазон)'
    parameter_name = 'amount_range'
    def lookups(self, request, model_admin):
        return (
            ('0-1000', 'до 1000'),
            ('1000-10000', '1000 – 10000'),
            ('10000-100000', '10000 – 100000'),
            ('100000+', 'более 100000'),
        )
    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        if self.value() == '0-1000':
            return queryset.filter(amount__lte=1000)
        if self.value() == '1000-10000':
            return queryset.filter(amount__gte=1000, amount__lte=10000)
        if self.value() == '10000-100000':
            return queryset.filter(amount__gte=10000, amount__lte=100000)
        if self.value() == '100000+':
            return queryset.filter(amount__gte=100000)
        return queryset


# Кастомный фильтр по дате с пресетами
class DatePresetFilter(admin.SimpleListFilter):
    title = 'дата (пресет)'
    parameter_name = 'date_preset'
    def lookups(self, request, model_admin):
        return (
            ('today', 'Сегодня'),
            ('week', 'Эта неделя'),
            ('month', 'Этот месяц'),
        )
    def queryset(self, request, queryset):
        today = timezone.now().date()
        if self.value() == 'today':
            return queryset.filter(transaction_date=today)
        if self.value() == 'week':
            week_start = today - timedelta(days=today.weekday())
            return queryset.filter(transaction_date__gte=week_start)
        if self.value() == 'month':
            return queryset.filter(transaction_date__year=today.year, transaction_date__month=today.month)
        return queryset

@admin.action(description='Восстановить из корзины')
def restore_transactions(modeladmin, request, queryset):
    restored = 0
    for obj in queryset.filter(deleted_at__isnull=False):
        TransactionService.restore_transaction(obj, request.user)
        restored += 1
    modeladmin.message_user(request, f'Восстановлено транзакций: {restored}.')

@admin.action(description='Экспортировать выбранные транзакции в CSV')
def export_transactions_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Пользователь', 'Дата', 'Тип', 'Сумма', 'Способ', 'Описание'])
    for t in queryset:
        writer.writerow([t.id, t.user.email, t.transaction_date, t.transaction_type, t.amount, t.payment_method, t.description])
    return response


@admin.action(description='Пересчитать ставки')
def recalc_tax_rates(modeladmin, request, queryset):
    updated = 0
    for tx in queryset:
        if tx.is_business and tx.activity_code:
            org_activity = OrganizationActivity.objects.filter(profile__user=tx.user, activity=tx.activity_code).first()
            if org_activity:
                new_cash = org_activity.cash_tax_rate
                new_non_cash = org_activity.non_cash_tax_rate
                if tx.cash_tax_rate != new_cash or tx.non_cash_tax_rate != new_non_cash:
                    tx.cash_tax_rate = new_cash
                    tx.non_cash_tax_rate = new_non_cash
                    tx.save(update_fields=['cash_tax_rate', 'non_cash_tax_rate'])
                    updated += 1
    modeladmin.message_user(request, f'Обновлено транзакций: {updated}')


class TransactionLogInline(admin.TabularInline):
    model = TransactionLog
    extra = 0
    fields = ('action', 'actor', 'created_at', 'note')
    readonly_fields = ('action', 'actor', 'created_at', 'note')
    can_delete = False


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    show_full_result_count = False
    list_select_related = ('user', 'category', 'activity_code')
    list_per_page = 100
    actions = [restore_transactions, export_transactions_csv, recalc_tax_rates]
    inlines = [TransactionLogInline]

    def get_queryset(self, request):
        qs = Transaction.all_objects.select_related('user', 'category', 'activity_code')
        return qs.order_by('-transaction_date', '-created_at')

    list_display = (
        'id',
        'user_link',
        'transaction_date',
        'transaction_type',
        'amount',
        'description_preview',
        'deleted_badge',
        'modified_by_short',
    )
    list_filter = (
            ('transaction_type', DropdownFilter),
            ('payment_method', DropdownFilter),
            ('is_business', DropdownFilter),
            ('is_taxable', DropdownFilter),
            ('user', RelatedDropdownFilter),
            TransactionDeletedFilter,
            AmountRangeFilter,
            DatePresetFilter,
    )
    search_fields = ('user__email', 'id', 'description', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user', 'category', 'activity_code')
    readonly_fields = ('created_at', 'updated_at', 'cash_tax_rate', 'non_cash_tax_rate')
    date_hierarchy = 'transaction_date'

    fieldsets = (
        (None, {'fields': ('user', 'transaction_type', 'amount', 'transaction_date')}),
        ('Классификация', {'fields': ('category', 'activity_code', 'payment_method', 'is_business', 'is_taxable')}),
        ('Детали', {'fields': ('description', 'deleted_at')}),
        ('Снимок ставок', {'fields': ('cash_tax_rate', 'non_cash_tax_rate'), 'classes': ('collapse',)}),
        ('Служебное', {'fields': ('created_at', 'updated_at', 'modified_by')}),
    )

    def save_model(self, request, obj, form, change):
        if change:
            obj.modified_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='Пользователь')
    def user_link(self, obj):
        url = reverse('admin:users_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)

    @admin.display(description='Кто изменил')
    def modified_by_short(self, obj):
        return obj.modified_by.email if obj.modified_by else '-'

    @admin.display(description='Описание')
    def description_preview(self, obj):
        text = (obj.description or '').strip()
        if len(text) <= 48:
            return text or '—'
        return text[:48] + '…'

    @admin.display(description='Статус', boolean=False)
    def deleted_badge(self, obj):
        if obj.deleted_at is None:
            return format_html('<span style="color:green;">активна</span>')
        return format_html('<span style="color:#c00;">удалена</span>')

    def delete_model(self, request, obj):
        if obj.deleted_at is None:
            TransactionService.soft_delete(obj, request.user)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if obj.deleted_at is None:
                TransactionService.soft_delete(obj, request.user)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category_type', 'user', 'is_system', 'created_at')
    list_filter = ('category_type', 'is_system')
    search_fields = ('name', 'user__email')
    raw_id_fields = ('user',)
    list_per_page = 100


@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_id', 'action', 'actor', 'created_at', 'note')
    list_filter = ('action',)
    search_fields = ('transaction__id', 'actor__email')
    readonly_fields = ('transaction', 'action', 'actor', 'created_at', 'note')
    raw_id_fields = ('transaction', 'actor')
    date_hierarchy = 'created_at'
    list_per_page = 100