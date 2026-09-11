"""Task 25: ตรวจสัญญาณเตือน (job ล้ม/stale, ingestion ล้ม, 5xx พุ่ง, AI ล้ม).

ออกแบบให้ cron เรียกถี่ ๆ (เช่นทุก 30 นาที) คู่กับ run_scheduled_jobs:
- พิมพ์ alerts ออก stdout เสมอ (exit 0)
- `--send` ส่งอีเมลผ่าน Django email backend ถ้าตั้งค่าไว้ (ไม่มี SMTP = log อย่างเดียว)
- `--fail` ให้ exit 1 เมื่อมี alert (ไว้ผูกกับ monitor ภายนอก)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from qa import metrics
from qa.jobs import get_job_freshness
from qa.models import JobRun

ALERT_5XX_THRESHOLD = 20


def collect_alerts(now=None):
    """คืน list ข้อความ alert (ไม่ส่งออกนอก ไม่ throw)."""
    from datetime import timedelta

    now = now or timezone.now()
    alerts = []
    day_ago = now - timedelta(hours=24)

    failed = list(
        JobRun.objects.filter(status="failed", last_run_at__gte=day_ago)
        .order_by("key")
        .values_list("key", "last_error")
    )
    for key, error in failed:
        first_line = (error or "").strip().splitlines()
        alerts.append(f"job ล้มเหลว: {key} ({first_line[0][:120] if first_line else 'ไม่ทราบสาเหตุ'})")

    for key, info in get_job_freshness().items():
        if info["is_stale"]:
            alerts.append(f"ข้อมูล stale: {info['title']} (สำเร็จล่าสุด {info['last_success_at']})")

    try:
        from news.ingestion import get_news_freshness

        news = get_news_freshness()
        if news["failure_newer"]:
            alerts.append("ดึงข่าว RSS ล้มเหลวล่าสุด (ใหม่กว่าความสำเร็จล่าสุด)")
    except Exception:
        pass

    counters = metrics.snapshot().get("counters", {})
    server_errors = sum(
        value for name, value in counters.items()
        if name.startswith("server_errors_total")
    )
    if server_errors >= ALERT_5XX_THRESHOLD:
        alerts.append(f"5xx พุ่ง: {server_errors} ครั้งในหน่วยความจำ process นี้")

    ai_errors = sum(
        value for name, value in counters.items()
        if name.startswith("external_ai_calls") and name.endswith("|error")
    )
    if ai_errors:
        alerts.append(f"เรียก AI ภายนอกล้มเหลว: {ai_errors} ครั้ง")

    return alerts


class Command(BaseCommand):
    help = "ตรวจสัญญาณเตือน (พิมพ์ออก stdout; --send ส่งอีเมลถ้าตั้ง SMTP ไว้)"

    def add_arguments(self, parser):
        parser.add_argument("--send", action="store_true")
        parser.add_argument("--fail", action="store_true")

    def handle(self, *args, **options):
        alerts = collect_alerts()
        if not alerts:
            self.stdout.write("ไม่พบสัญญาณเตือน")
            return
        for alert in alerts:
            self.stdout.write(self.style.WARNING(f"ALERT: {alert}"))
        if options["send"]:
            self._send_mail(alerts)
        if options["fail"]:
            raise SystemExit(1)

    def _send_mail(self, alerts):
        try:
            from django.core.mail import mail_admins

            mail_admins(
                "[เลขเด็ดเอไอ] alerts",
                "\n".join(f"- {a}" for a in alerts),
            )
            self.stdout.write("ส่งอีเมลแจ้งเตือนแล้ว")
        except Exception as exc:  # ไม่มี SMTP = log ไว้ ไม่ล้ม
            import logging

            logging.getLogger(__name__).warning("ส่งอีเมลเตือนไม่สำเร็จ: %r", exc)
