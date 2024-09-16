from django.db import models
import uuid
# Create your models here.

class Conversation(models.Model):
    user_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        primary_key=True
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    conversation = models.ForeignObject(
        Conversation,
        related_name="messages",
        on_delete=models.CASCADE
    )
    content = models.TextField()
    is_user = models.BooleanField(True)
    created_at = models.DateTimeField(auto_now_add=True)
