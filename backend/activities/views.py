from django.shortcuts import render
from rest_framework import viewsets, generics, status, filters
from rest_framework.permissions import IsAuthenticated
from activities.models import ActivityCode
from activities.serializers import ActivityCodeSerializer


class ActivityCodeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint для просмотра справочника ГКЭД (ОКЭД).
    Доступен всем, чтобы можно было выбрать вид деятельности при регистрации/онбординге.
    """
    queryset = ActivityCode.objects.all()
    serializer_class = ActivityCodeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'name']