from rest_framework import serializers

class TgLinkSerializer(serializers.Serializer):
    link = serializers.URLField(read_only=True)

class TgConfirmSerializer(serializers.Serializer):
    code = serializers.UUIDField(write_only=True)
    telegram_id = serializers.CharField(write_only=True)
    email = serializers.EmailField(read_only=True)

class TgAuthSerializer(serializers.Serializer):
    telegram_id = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
