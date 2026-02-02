from drf_yasg import openapi
from .serializers import (
    TransactionSerializer,
    CategorySerializer,
    TransactionSummarySerializer,
)


# Category schemas
CATEGORY_LIST_RESP = {200: CategorySerializer(many=True)}
CATEGORY_DETAIL_RESP = {200: CategorySerializer}
CATEGORY_CREATE_REQ = CategorySerializer
CATEGORY_CREATE_RESP = {201: CategorySerializer, 400: 'Bad Request'}
CATEGORY_UPDATE_RESP = {200: CategorySerializer, 403: 'Forbidden', 400: 'Bad Request'}
CATEGORY_DELETE_RESP = {204: 'No Content', 403: 'Forbidden'}


# Transaction schemas / params
TRANSACTION_LIST_PARAMS = [
    openapi.Parameter('type', openapi.IN_QUERY, description='income|expense', type=openapi.TYPE_STRING),
    openapi.Parameter('category_id', openapi.IN_QUERY, description='Category ID', type=openapi.TYPE_INTEGER),
    openapi.Parameter('date_from', openapi.IN_QUERY, description='YYYY-MM-DD', type=openapi.TYPE_STRING, format='date'),
    openapi.Parameter('date_to', openapi.IN_QUERY, description='YYYY-MM-DD', type=openapi.TYPE_STRING, format='date'),
    openapi.Parameter('ordering', openapi.IN_QUERY, description='Ordering field, e.g. -amount', type=openapi.TYPE_STRING),
]

TRANSACTION_LIST_RESP = {200: TransactionSerializer(many=True)}
TRANSACTION_DETAIL_RESP = {200: TransactionSerializer}
TRANSACTION_CREATE_REQ = TransactionSerializer
TRANSACTION_CREATE_RESP = {201: TransactionSerializer, 400: 'Bad Request'}
TRANSACTION_UPDATE_RESP = {200: TransactionSerializer, 400: 'Bad Request'}
TRANSACTION_DELETE_RESP = {204: 'No Content'}


# Summary params / response
SUMMARY_PARAMS = [
    openapi.Parameter(
        'period',
        openapi.IN_QUERY,
        description="Период для сводки",
        type=openapi.TYPE_STRING,
        enum=['day', 'week', 'month', 'year'],
        default='month'
    ),
    openapi.Parameter(
        'date_from',
        openapi.IN_QUERY,
        description="Начальная дата (YYYY-MM-DD). Если указана, period игнорируется",
        type=openapi.TYPE_STRING,
        format='date'
    ),
    openapi.Parameter(
        'date_to',
        openapi.IN_QUERY,
        description="Конечная дата (YYYY-MM-DD). Если указана, period игнорируется",
        type=openapi.TYPE_STRING,
        format='date'
    ),
]

SUMMARY_RESP = {
    200: TransactionSummarySerializer,
    400: "Некорректные параметры запроса",
}


# By-category response schema
BY_CATEGORY_ITEM = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'category__id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Category ID', nullable=True),
        'category__name': openapi.Schema(type=openapi.TYPE_STRING, description='Category name', nullable=True),
        'transaction_type': openapi.Schema(type=openapi.TYPE_STRING, description='income|expense'),
        'total_amount': openapi.Schema(type=openapi.TYPE_STRING, description='Total amount as decimal string'),
        'transaction_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of transactions'),
    }
)

BY_CATEGORY_RESP = {200: openapi.Schema(type=openapi.TYPE_ARRAY, items=BY_CATEGORY_ITEM)}
