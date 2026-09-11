from django.contrib import admin
from django.utils import timezone

from qa.models import BetaInvite, JobRun, SystemFlag


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    list_display = [
        "key", "title", "status", "last_success_at",
        "consecutive_failures", "next_run_at",
    ]
    list_filter = ["status"]
    search_fields = ["key", "title"]
    readonly_fields = [
        "key", "last_run_at", "last_success_at", "last_error",
        "consecutive_failures", "attempts_left", "next_run_at",
        "locked_at", "last_duration_seconds",
    ]


@admin.register(BetaInvite)
class BetaInviteAdmin(admin.ModelAdmin):
    list_display = ["code", "label", "max_uses", "used_count", "is_active", "last_used_at"]
    list_filter = ["is_active"]
    search_fields = ["code", "label"]
    readonly_fields = ["used_count", "created_at", "last_used_at"]


@admin.register(SystemFlag)
class SystemFlagAdmin(admin.ModelAdmin):
    list_display = ["key", "level", "message", "is_active", "created_at", "resolved_at"]
    list_filter = ["level", "is_active"]
    search_fields = ["key", "message"]
    readonly_fields = ["created_at"]
    actions = ["resolve_flags"]

    @admin.action(description="ปิดเหตุที่เลือก")
    def resolve_flags(self, request, queryset):
        queryset.update(is_active=False, resolved_at=timezone.now())
