"""Task 24: ทะเบียนงานตามตาราง (version-controlled) + ตัวช่วย freshness/lock.

รันผ่าน `manage.py run_scheduled_jobs` (cron/systemd timer เรียกถี่ ๆ เช่นทุก 15 นาที)
แต่ละ job ระบุ schedule/owner/retry/timeout/freshness ครบ.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from qa.models import JobRun

# key, title, owner, argv (manage.py ...), interval, retry, timeout, freshness
JOB_REGISTRY = [
    {
        "key": "lotto_sync",
        "title": "ซิงค์ผลหวยเข้า lotto_stats",
        "owner": "lottery",
        "argv": ["sync_lotto_data", "--days-back", "30"],
        "interval_hours": 24,
        "retry_delay_minutes": 60,
        "max_retries": 3,
        "timeout_seconds": 600,
        "freshness_hours": 48,
    },
    {
        "key": "rss_ingest",
        "title": "ดึงข่าว RSS",
        "owner": "news",
        "argv": ["scrape_rss_feeds", "--limit", "20"],
        "interval_hours": 6,
        "retry_delay_minutes": 30,
        "max_retries": 3,
        "timeout_seconds": 600,
        "freshness_hours": 12,
    },
    {
        "key": "category_fallback",
        "title": "ขูดข่าว fallback (เฉพาะเมื่อ RSS เงียบ)",
        "owner": "news",
        "argv": ["scrape_category", "--limit", "5"],
        "interval_hours": 12,
        "retry_delay_minutes": 60,
        "max_retries": 2,
        "timeout_seconds": 600,
        "freshness_hours": 48,
    },
    {
        "key": "ai_generate",
        "title": "สร้างการทำนาย AI งวดถัดไป",
        "owner": "ai",
        "argv": ["generate_ai_prediction"],
        "interval_hours": 24,
        "retry_delay_minutes": 120,
        "max_retries": 2,
        "timeout_seconds": 1200,
        "freshness_hours": 48,
    },
    {
        "key": "accuracy_reconcile",
        "title": "ตรวจผลย้อนหลังสูตร",
        "owner": "formula",
        "argv": ["verify_formula_predictions"],
        "interval_hours": 24,
        "retry_delay_minutes": 60,
        "max_retries": 2,
        "timeout_seconds": 600,
        "freshness_hours": 72,
    },
    {
        "key": "dreams_cleanup",
        "title": "ลบประวัติฝันเกิน retention",
        "owner": "privacy",
        "argv": ["cleanup_old_dreams"],
        "interval_hours": 168,
        "retry_delay_minutes": 120,
        "max_retries": 2,
        "timeout_seconds": 600,
        "freshness_hours": 336,
    },
]


def get_job(key):
    for job in JOB_REGISTRY:
        if job["key"] == key:
            return job
    return None


def due_jobs(now=None):
    """งานที่ถึงกำหนด (next_run_at ว่างหรือผ่านมาแล้ว)."""
    now = now or timezone.now()
    due = []
    for job in JOB_REGISTRY:
        try:
            row = JobRun.objects.get(key=job["key"])
        except JobRun.DoesNotExist:
            due.append(job)
            continue
        if row.next_run_at is None or row.next_run_at <= now:
            due.append(job)
    return due


def acquire_lock(job, now=None):
    """ล็อกกันรันทับ (atomic). คืน JobRun ถ้าได้ล็อก, None ถ้ามีตัวรันอยู่.

    ล็อกค้างเกิน timeout ของ job ถือว่าตายแล้ว ยึดได้ (stale takeover).
    """
    from qa.models import JobRun as JobRunModel

    now = now or timezone.now()
    timeout = timedelta(seconds=job["timeout_seconds"])
    with transaction.atomic():
        row, _ = JobRunModel.objects.select_for_update().get_or_create(
            key=job["key"],
            defaults={
                "title": job["title"],
                "owner": job["owner"],
                "attempts_left": job["max_retries"],
            },
        )
        if (
            row.status == "running"
            and row.locked_at
            and (now - row.locked_at) < timeout
        ):
            return None
        row.status = "running"
        row.locked_at = now
        row.last_run_at = now
        row.title = job["title"]
        row.owner = job["owner"]
        row.save()
        return row


def get_job_freshness():
    """{key: {title, last_success_at, is_stale}} สำหรับ UI/admin."""
    out = {}
    for job in JOB_REGISTRY:
        try:
            row = JobRun.objects.get(key=job["key"])
        except JobRun.DoesNotExist:
            out[job["key"]] = {
                "title": job["title"],
                "last_success_at": None,
                "is_stale": False,  # ยังไม่เคยรัน = ไม่มีข้อมูลตัดสิน ไม่ใช่ stale
            }
            continue
        out[job["key"]] = {
            "title": job["title"],
            "last_success_at": row.last_success_at,
            "is_stale": row.last_success_at is not None
            and not row.is_fresh(job["freshness_hours"]),
        }
    return out
