from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from finance.models import Transaction
from users.models import CustomUser
from organization.models import OrganizationProfile

@staff_member_required
def support_dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    total_users = CustomUser.objects.count()
    incomplete_onboarding = OrganizationProfile.objects.filter(~Q(onboarding_status='completed')).count()
    total_transactions = Transaction.objects.count()
    deleted_transactions = Transaction.all_objects.filter(deleted_at__isnull=False).count()

    transactions_today = Transaction.objects.filter(transaction_date=today).count()
    income_today = Transaction.objects.filter(
        transaction_date=today,
        transaction_type='income'
    ).aggregate(s=Sum('amount'))['s'] or 0

    recent_transactions = Transaction.all_objects.select_related('user').order_by('-created_at')[:10]

    context = {
        'total_users': total_users,
        'incomplete_onboarding': incomplete_onboarding,
        'total_transactions': total_transactions,
        'deleted_transactions': deleted_transactions,
        'transactions_today': transactions_today,
        'income_today': income_today,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'admin/support_dashboard.html', context)