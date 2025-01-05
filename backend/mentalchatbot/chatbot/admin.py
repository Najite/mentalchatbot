from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    fields = ('input', 'response', 'timestamp')
    readonly_fields = ('input', 'response', 'timestamp')
    extra = 0

class ConversationAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'created_at')
    inlines = [MessageInline]

admin.site.register(Conversation, ConversationAdmin)
