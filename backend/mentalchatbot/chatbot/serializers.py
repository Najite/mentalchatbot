from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['content', 'is_user', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True)
    class Meta:
        model = Conversation
        fields = ['id', 'user_id', 'messages', 'created_at']



class ChatRequestSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=1000)
