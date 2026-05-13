"""
Админка: поддержка пользователей + минимизация лишнего доступа к данным.

- Удаление транзакции в списке/форме = мягкое удаление (как в API), не CASCADE.
- Восстановление: действие «Восстановить из корзины» или очистить deleted_at вручную.
- Журнал по каждой транзакции — инлайн; отдельный раздел «Журнал транзакций» — обзор по всем.
"""

from django.contrib import admin
from django.utils.html import format_html

from finance.models import Category, Transaction, TransactionLog
from finance.services.transaction_service import TransactionService


class TransactionDeletedFilter(admin.SimpleListFilter):
    title = 'корзина'
    parameter_name = 'trash'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Только активные'),
            ('deleted', 'Только удалённые (мягко)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'deleted':
            return queryset.filter(deleted_at__isnull=False)
        if self.value() == 'active':
            return queryset.filter(deleted_at__isnull=True)
        return queryset


class TransactionLogInline(admin.TabularInline):
    model = TransactionLog
    extra = 0
    fields = ('action', 'actor', 'created_at', 'note')
    readonly_fields = ('action', 'actor', 'created_at', 'note')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category_type', 'user', 'is_system', 'created_at')
    list_filter = ('category_type', 'is_system')
    search_fields = ('name', 'user__email')
    raw_id_fields = ('user',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Все транзакции включая удалённые — для восстановления и разбора обращений."""

    show_full_result_count = False
    actions = ('restore_transactions',)
    inlines = (TransactionLogInline,)

    def get_queryset(self, request):
        return (
            Transaction.all_objects
            .select_related('user', 'category', 'activity_code')
            .order_by('-transaction_date', '-created_at')
        )

    list_display = (
        'id',
        'user_email',
        'transaction_date',
        'transaction_type',
        'amount',
        'description_preview',
        'deleted_badge',
    )
    list_filter = ('transaction_type', 'payment_method', 'is_business', 'is_taxable', TransactionDeletedFilter)
    search_fields = ('user__email', 'id')
    raw_id_fields = ('user', 'category', 'activity_code')
    readonly_fields = ('created_at', 'updated_at', 'cash_tax_rate', 'non_cash_tax_rate')
    date_hierarchy = 'transaction_date'

    fieldsets = (
        (None, {'fields': ('user', 'transaction_type', 'amount', 'transaction_date')}),
        ('Классификация', {'fields': ('category', 'activity_code', 'payment_method', 'is_business', 'is_taxable')}),
        ('Детали', {'fields': ('description', 'deleted_at')}),
        ('Снимок ставок', {'fields': ('cash_tax_rate', 'non_cash_tax_rate'), 'classes': ('collapse',)}),
        ('Служебное', {'fields': ('created_at', 'updated_at')}),
    )

    def delete_model(self, request, obj):
        if obj.deleted_at is None:
            TransactionService.soft_delete(obj, request.user)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if obj.deleted_at is None:
                TransactionService.soft_delete(obj, request.user)

    @admin.action(description='Восстановить из корзины (выбранные)')
    def restore_transactions(self, request, queryset):
        restored = 0
        for obj in queryset.filter(deleted_at__isnull=False):
            TransactionService.restore_transaction(obj, request.user)
            restored += 1
        self.message_user(request, f'Восстановлено транзакций: {restored}.')

    @admin.display(description='Пользователь')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Описание (фрагмент)')
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


@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_id', 'action', 'actor', 'created_at', 'note')
    list_filter = ('action',)
    search_fields = ('transaction__id', 'actor__email')
    readonly_fields = ('transaction', 'action', 'actor', 'created_at', 'note')
    raw_id_fields = ('transaction', 'actor')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
