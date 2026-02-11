# aichat/serializers.py
from rest_framework import serializers

class ChatSerializer(serializers.Serializer):
    text = serializers.CharField()
