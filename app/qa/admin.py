from django.contrib import admin

from qa.models import JobRun


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
