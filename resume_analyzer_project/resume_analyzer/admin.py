from django.contrib import admin
from .models import Resume, ChatMessage

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'file_hash', 'uploaded_at', 'vector_namespace')
    search_fields = ('original_filename', 'file_hash')
    readonly_fields = ('file_hash', 'vector_namespace')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('resume', 'message_type', 'short_content', 'timestamp')
    list_filter = ('message_type', 'timestamp')
    search_fields = ('content',)

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    short_content.short_description = 'Content'
