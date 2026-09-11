from django.contrib import admin
from .models import HomePage, ContactMessage

admin.site.register(HomePage)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["message_type", "name", "status", "created_at"]
    list_filter = ["message_type", "status"]
    search_fields = ["name", "contact", "message"]
    readonly_fields = ["created_at"]