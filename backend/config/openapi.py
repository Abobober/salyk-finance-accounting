# core/openapi.py
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from drf_spectacular.generators import SpectacularAutoSchema

class SafeAutoSchema(SpectacularAutoSchema):
    """
    Авто-схема для безопасной генерации Swagger, 
    обходя динамические querysets и request.user зависимости
    """
    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        # безопасно подставляем пустые queryset для PrimaryKeyRelatedField
        for field in serializer.fields.values():
            try:
                if hasattr(field, 'queryset') and field.queryset is None:
                    field.queryset = []
            except Exception:
                # игнорируем любые ошибки
                field.queryset = []
        return serializer
