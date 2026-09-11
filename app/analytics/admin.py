from django.contrib import admin

from .models import AnalyticsEvent


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ["name", "session_id", "draw_period", "created_at"]
    list_filter = ["name", "draw_period"]
    search_fields = ["session_id"]
    date_hierarchy = "created_at"
    readonly_fields = ["name", "session_id", "draw_period", "created_at"]

    def has_add_permission(self, request):
        return False
