from rest_framework import serializers

class ChatSerializer(serializers.Serializer):
    message = serializers.CharField()
    previous_assistant = serializers.DictField(required=False)
