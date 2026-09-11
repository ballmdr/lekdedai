"""Task 25: health check สาธารณะ + metrics สำหรับ staff."""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from qa import metrics
from qa.jobs import get_job_freshness
from qa.rollout import (
    BETA_ACCESS_SESSION_KEY,
    gate_enabled,
    get_beta_status,
    mark_beta_access,
    redeem_beta_code,
)
from utils.rate_limit import ratelimit


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


def _safe_next(request, candidate, default="/"):
    """กัน open redirect: ยอมเฉพาะ path ในโดเมนเดียวกัน."""
    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return default


@ratelimit("20/m")
@require_http_methods(["GET", "POST"])
def beta_gate(request):
    """GET/POST /beta/ — กรอกรหัสเชิญเข้า closed beta (Task 30)."""
    if not gate_enabled():
        return redirect("home")

    status = get_beta_status()
    if status["state"] == "closed":
        return redirect("qa:beta_closed")

    nxt = request.POST.get("next") or request.GET.get("next") or ""
    if request.session.get(BETA_ACCESS_SESSION_KEY):
        return redirect(_safe_next(request, nxt))

    error = ""
    if request.method == "POST":
        invite = redeem_beta_code(request.POST.get("code", ""))
        if invite is not None:
            mark_beta_access(request, invite.code)
            messages.success(request, "ยืนยันรหัสแล้ว ยินดีต้อนรับสู่ช่วง beta")
            return redirect(_safe_next(request, nxt))
        error = "รหัสเชิญไม่ถูกต้อง หมดอายุ หรือถูกใช้ครบแล้ว"

    return render(request, "qa/beta_gate.html", {
        "page_title": "ช่วงทดลองใช้งาน (closed beta) - เลขเด็ดเอไอ",
        "error": error,
        "next": nxt,
        "status": status,
    })


def beta_closed(request):
    """GET /beta/closed/ — ประกาศว่าระบบหยุดรับชั่วคราว (kill switch/P0)."""
    status = get_beta_status()
    return render(request, "qa/beta_closed.html", {
        "page_title": "ระบบปิดชั่วคราว - เลขเด็ดเอไอ",
        "status": status,
    })
