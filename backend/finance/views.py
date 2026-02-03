from django.db.models import Sum
from django.utils.decorators import method_decorator
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer
from .permissions import IsCategoryOwnerOrSystemReadOnly
from .filters import TransactionFilter


@method_decorator(
    name='list',
    decorator=swagger_auto_schema(
        operation_description="List categories"
    )
)
@method_decorator(
    name='retrieve',
    decorator=swagger_auto_schema(
        operation_description="Retrieve category details"
    )
)
@method_decorator(
    name='create',
    decorator=swagger_auto_schema(
        operation_description="Create a new category",
        request_body=CategorySerializer
    )
)
@method_decorator(
    name='update',
    decorator=swagger_auto_schema(
        operation_description="Update category",
        request_body=CategorySerializer
    )
)
@method_decorator(
    name='partial_update',
    decorator=swagger_auto_schema(
        operation_description="Partially update category",
        request_body=CategorySerializer
    )
)
@method_decorator(
    name='destroy',
    decorator=swagger_auto_schema(
        operation_description="Delete category"
    )
)
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsCategoryOwnerOrSystemReadOnly]

    def get_queryset(self):
        return Category.objects.filter(
            user=self.request.user
        ) | Category.objects.filter(is_system=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@method_decorator(
    name='list',
    decorator=swagger_auto_schema(
        operation_description="List transactions"
    )
)
@method_decorator(
    name='retrieve',
    decorator=swagger_auto_schema(
        operation_description="Retrieve transaction details"
    )
)
@method_decorator(
    name='create',
    decorator=swagger_auto_schema(
        operation_description="Create transaction",
        request_body=TransactionSerializer
    )
)
@method_decorator(
    name='update',
    decorator=swagger_auto_schema(
        operation_description="Update transaction",
        request_body=TransactionSerializer
    )
)
@method_decorator(
    name='partial_update',
    decorator=swagger_auto_schema(
        operation_description="Partially update transaction",
        request_body=TransactionSerializer
    )
)
@method_decorator(
    name='destroy',
    decorator=swagger_auto_schema(
        operation_description="Delete transaction"
    )
)
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = TransactionFilter
    ordering_fields = ['transaction_date', 'amount', 'created_at']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
    operation_description="Get transaction summary grouped by category",
    responses={200: 'Summary'}
    )
    @action(detail=False, methods=['get'])
    def summary_by_category(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        summary = (
            queryset
            .values('category__name')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )

        return Response(summary)