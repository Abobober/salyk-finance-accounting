from rest_framework import serializers

class ChatSessionSerializer(serializers.Serializer):
    message = serializers.CharField()
    session_id = serializers.CharField(required=True)
