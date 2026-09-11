"""Task 25: health check สาธารณะ + metrics สำหรับ staff."""
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse
from django.utils import timezone

from qa import metrics
from qa.jobs import get_job_freshness


def _db_ok():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, f"database unreachable: {type(exc).__name__}"


def _pending_migrations():
    try:
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        return len(plan)
    except Exception:
        return -1


def health(request):
    """GET /health/ — สาธารณะ ตอบ 200 ok / 503 degraded (ไม่มีข้อมูลลับ)."""
    from qa.models import JobRun

    db_ok, db_error = _db_ok()
    pending = _pending_migrations()
    failed_jobs = list(
        JobRun.objects.filter(status="failed").values_list("key", flat=True)[:10]
    )
    freshness = get_job_freshness()
    stale_jobs = sorted(
        key for key, info in freshness.items() if info["is_stale"]
    )

    problems = []
    if not db_ok:
        problems.append(db_error or "database error")
    if pending and pending > 0:
        problems.append(f"{pending} pending migrations")
    if failed_jobs:
        problems.append(f"failed jobs: {', '.join(failed_jobs)}")
    if stale_jobs:
        problems.append(f"stale jobs: {', '.join(stale_jobs)}")

    try:
        from news.ingestion import get_news_freshness

        news = get_news_freshness()
        if news["failure_newer"]:
            problems.append("news ingestion failing")
        elif news["is_stale"] and news["latest_fetched"] is not None:
            problems.append("news data stale")
    except Exception:
        pass

    status = "ok" if not problems else "degraded"
    return JsonResponse(
        {
            "status": status,
            "timestamp": timezone.now().isoformat(),
            "problems": problems,
        },
        status=200 if status == "ok" else 503,
    )


@staff_member_required
def metrics_view(request):
    """GET /metrics/ — staff เท่านั้น (ตัวเลขรวม ไม่มี PII)."""
    return JsonResponse(metrics.snapshot())
