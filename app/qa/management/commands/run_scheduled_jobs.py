"""Task 24: tick รันงานที่ถึงกำหนด (เรียกถี่ ๆ จาก cron/systemd timer).

แต่ละ job รันใน subprocess แยก (`manage.py <argv>`) พร้อม timeout จริง —
timeout แล้ว kill ทิ้ง บันทึกผลลง JobRun ไม่ throw ออกนอก (exit 0 เสมอ
ยกเว้นพังระดับ runner เอง).
"""
import os
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from qa.jobs import JOB_REGISTRY, acquire_lock, due_jobs, get_job


def _project_root():
    # settings.BASE_DIR = app/ -> root = parent
    return Path(settings.BASE_DIR).parent


def _decode(data):
    if not data:
        return ""
    if isinstance(data, str):
        return data
    return data.decode("utf-8", errors="replace")


def _run_argv(argv, timeout_seconds):
    """รัน manage.py argv ใน process แยกพร้อม timeout. คืน (ok, output_tail, seconds)."""
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, "app/manage.py", *argv],
            cwd=_project_root(),
            env=os.environ.copy(),
            capture_output=True,
            timeout=timeout_seconds,
        )
        seconds = time.monotonic() - started
        tail = (_decode(proc.stdout) + _decode(proc.stderr))[-2000:]
        return proc.returncode == 0, tail, seconds
    except subprocess.TimeoutExpired as exc:
        seconds = time.monotonic() - started
        out = _decode(exc.stdout)
        return False, (f"TIMEOUT เกิน {timeout_seconds} วินาที\n" + out)[-2000:], seconds


class Command(BaseCommand):
    help = "รันงานตามตารางที่ถึงกำหนด (idempotent, มี lock/retry/timeout)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--job", type=str, default=None, help="รันเฉพาะ job key นี้"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="บังคับรันแม้ยังไม่ถึงกำหนด (ยังเคารพ lock)",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        if options["job"]:
            job = get_job(options["job"])
            if job is None:
                self.stdout.write(self.style.ERROR(f"ไม่พบ job: {options['job']}"))
                return
            jobs = [job]
        else:
            jobs = due_jobs(now)
            if options["force"]:
                jobs = list(JOB_REGISTRY)

        if not jobs:
            self.stdout.write("ไม่มีงานถึงกำหนด")
            return

        for job in jobs:
            self._run_one(job, now)

    def _run_one(self, job, now):
        from qa.models import JobRun

        row = acquire_lock(job, now)
        if row is None:
            self.stdout.write(f"ข้าม {job['key']}: มีตัวรันอยู่แล้ว")
            return

        self.stdout.write(f"รัน {job['key']}: manage.py {' '.join(job['argv'])}")
        ok, output, seconds = _run_argv(job["argv"], job["timeout_seconds"])

        row.last_duration_seconds = round(seconds, 1)
        row.locked_at = None
        if ok:
            row.status = "success"
            row.last_success_at = timezone.now()
            row.last_error = ""
            row.consecutive_failures = 0
            row.attempts_left = job["max_retries"]
            row.next_run_at = timezone.now() + timedelta(hours=job["interval_hours"])
            self.stdout.write(self.style.SUCCESS(f"OK {job['key']} ({seconds:.0f}s)"))
        else:
            row.consecutive_failures += 1
            left = max(0, row.attempts_left - 1)
            row.attempts_left = left
            row.last_error = output[-1000:]
            if left > 0:
                row.status = "failed"
                row.next_run_at = timezone.now() + timedelta(
                    minutes=job["retry_delay_minutes"]
                )
                self.stdout.write(
                    self.style.WARNING(
                        f"ล้มเหลว {job['key']} — ลองใหม่ใน {job['retry_delay_minutes']} นาที "
                        f"(เหลือ {left} ครั้ง)"
                    )
                )
            else:
                row.status = "failed"
                row.attempts_left = job["max_retries"]
                row.next_run_at = timezone.now() + timedelta(hours=job["interval_hours"])
                self.stdout.write(
                    self.style.ERROR(f"ล้มเหลว {job['key']} — หมดโควตาลองซ้ำ รอรอบถัดไป")
                )
        row.save()
