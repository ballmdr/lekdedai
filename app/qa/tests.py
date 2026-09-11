"""Task 24: lock/retry/timeout/freshness ของ scheduler."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from qa.jobs import JOB_REGISTRY, acquire_lock, due_jobs, get_job, get_job_freshness
from qa.models import JobRun

FAKE_JOB = {
    "key": "test-job",
    "title": "Test",
    "owner": "qa",
    "argv": ["check"],
    "interval_hours": 24,
    "retry_delay_minutes": 30,
    "max_retries": 2,
    "timeout_seconds": 60,
    "freshness_hours": 48,
}

FAIL_JOB = dict(
    FAKE_JOB, key="test-fail", argv=["migrate", "--bad-flag"],
)


class RegistryTests(TestCase):
    def test_registry_complete(self):
        keys = set()
        required = {
            "key", "title", "owner", "argv", "interval_hours",
            "retry_delay_minutes", "max_retries", "timeout_seconds",
            "freshness_hours",
        }
        for job in JOB_REGISTRY:
            self.assertTrue(required.issubset(job), job.get("key"))
            self.assertNotIn(job["key"], keys)
            keys.add(job["key"])
            self.assertTrue(job["argv"])
            self.assertGreater(job["interval_hours"], 0)
            self.assertGreater(job["timeout_seconds"], 0)

    def test_get_job(self):
        self.assertIsNotNone(get_job("lotto_sync"))
        self.assertIsNone(get_job("nope"))


class LockTests(TestCase):
    def test_second_acquire_skipped(self):
        now = timezone.now()
        self.assertIsNotNone(acquire_lock(FAKE_JOB, now))
        self.assertIsNone(acquire_lock(FAKE_JOB, now))

    def test_stale_lock_takeover(self):
        now = timezone.now()
        JobRun.objects.create(
            key="test-job", status="running",
            locked_at=now - timedelta(seconds=FAKE_JOB["timeout_seconds"] + 10),
        )
        self.assertIsNotNone(acquire_lock(FAKE_JOB, now))

    def test_due_jobs(self):
        self.assertIn("lotto_sync", [j["key"] for j in due_jobs()])
        JobRun.objects.create(
            key="lotto_sync", next_run_at=timezone.now() + timedelta(hours=1)
        )
        self.assertNotIn("lotto_sync", [j["key"] for j in due_jobs()])


class RunnerTests(TestCase):
    def _run_one(self, job):
        from qa.management.commands.run_scheduled_jobs import Command

        Command()._run_one(dict(job), timezone.now())
        return JobRun.objects.get(key=job["key"])

    def test_success_records(self):
        row = self._run_one(FAKE_JOB)
        self.assertEqual(row.status, "success")
        self.assertIsNotNone(row.last_success_at)
        self.assertIsNotNone(row.next_run_at)
        self.assertEqual(row.consecutive_failures, 0)
        self.assertIsNotNone(row.last_duration_seconds)

    def test_failure_retries_then_waits(self):
        row = self._run_one(FAIL_JOB)
        self.assertEqual(row.status, "failed")
        self.assertEqual(row.consecutive_failures, 1)
        self.assertEqual(row.attempts_left, 1)
        first_retry = row.next_run_at
        row = self._run_one(FAIL_JOB)
        self.assertEqual(row.attempts_left, 2)  # รีเซ็ตหลังหมดโควตา
        self.assertGreater(row.next_run_at, first_retry)

    def test_rerun_no_duplicate_rows(self):
        self._run_one(FAKE_JOB)
        self._run_one(FAKE_JOB)
        self.assertEqual(JobRun.objects.filter(key="test-job").count(), 1)

    def test_timeout_kills_and_records(self):
        job = dict(
            FAKE_JOB,
            key="test-slow",
            argv=["shell", "-c", "import time; time.sleep(30)"],
            timeout_seconds=3,
        )
        row = self._run_one(job)
        self.assertEqual(row.status, "failed")
        self.assertIn("TIMEOUT", row.last_error)

    def test_command_runs_real_registry_job(self):
        from django.core.management import call_command

        call_command("run_scheduled_jobs", job="dreams_cleanup")
        row = JobRun.objects.get(key="dreams_cleanup")
        self.assertEqual(row.status, "success")


class FreshnessTests(TestCase):
    def test_never_run_is_not_stale(self):
        info = get_job_freshness()["lotto_sync"]
        self.assertIsNone(info["last_success_at"])
        self.assertFalse(info["is_stale"])

    def test_recent_success_fresh_old_stale(self):
        now = timezone.now()
        JobRun.objects.create(key="lotto_sync", last_success_at=now)
        self.assertFalse(get_job_freshness()["lotto_sync"]["is_stale"])
        JobRun.objects.filter(key="lotto_sync").update(
            last_success_at=now - timedelta(hours=49)
        )
        self.assertTrue(get_job_freshness()["lotto_sync"]["is_stale"])

    def test_stats_page_shows_sync_freshness(self):
        from datetime import date

        from lotto_stats.models import LotteryDraw

        LotteryDraw.objects.create(
            draw_date=date(2026, 9, 1), first_prize="417212", two_digit="12",
        )
        JobRun.objects.create(
            key="lotto_sync", last_success_at=timezone.now()
        )
        res = self.client.get("/lotto_stats/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "ซิงค์อัตโนมัติล่าสุด")

    def test_stats_page_shows_stale_warning(self):
        from datetime import date

        from lotto_stats.models import LotteryDraw

        LotteryDraw.objects.create(
            draw_date=date(2026, 9, 1), first_prize="417212", two_digit="12",
        )
        JobRun.objects.create(
            key="lotto_sync",
            last_success_at=timezone.now() - timedelta(hours=50),
        )
        res = self.client.get("/lotto_stats/")
        self.assertContains(res, "ล่าช้าเกินกำหนด")


class HealthEndpointTests(TestCase):
    """Task 25: /health/ สาธารณะ 200 ok / 503 degraded."""

    def test_healthy(self):
        res = self.client.get("/health/")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["problems"], [])

    def test_degraded_on_failed_job(self):
        JobRun.objects.create(key="rss_ingest", status="failed")
        res = self.client.get("/health/")
        self.assertEqual(res.status_code, 503)
        body = res.json()
        self.assertEqual(body["status"], "degraded")
        self.assertTrue(any("rss_ingest" in p for p in body["problems"]))


class MetricsTests(TestCase):
    """Task 25: middleware เก็บสถิติ, /metrics/ staff-only."""

    def setUp(self):
        from qa import metrics

        metrics.reset()

    def test_requests_counted_with_latency(self):
        from qa import metrics

        self.client.get("/notebook/")
        snap = metrics.snapshot()
        self.assertIn("requests_total{notebook:index|2xx}", snap["counters"])
        self.assertIn("notebook:index", snap["latency_avg_seconds"])

    def test_metrics_staff_only(self):
        res = self.client.get("/metrics/")
        self.assertEqual(res.status_code, 302)
        from django.contrib.auth import get_user_model

        staff = get_user_model().objects.create_user(
            "staff", password="pw", is_staff=True
        )
        self.client.force_login(staff)
        res = self.client.get("/metrics/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("counters", res.json())

    def test_json_formatter(self):
        import json
        import logging

        from qa.logging import JSONFormatter

        record = logging.LogRecord(
            "test", logging.ERROR, __file__, 1, "boom %s", ("x",), None
        )
        payload = json.loads(JSONFormatter().format(record))
        self.assertEqual(
            (payload["level"], payload["logger"], payload["message"]),
            ("ERROR", "test", "boom x"),
        )
        self.assertIn("timestamp", payload)


class AlertTests(TestCase):
    """Task 25: fault injection แล้ว alert ต้องจับได้."""

    def setUp(self):
        from qa import metrics

        metrics.reset()

    def test_no_alerts_when_healthy(self):
        from qa.management.commands.check_alerts import collect_alerts

        self.assertEqual(collect_alerts(), [])

    def test_failed_job_alert(self):
        from qa.management.commands.check_alerts import collect_alerts

        JobRun.objects.create(
            key="rss_ingest", status="failed",
            last_run_at=timezone.now(), last_error="boom",
        )
        alerts = collect_alerts()
        self.assertTrue(any("rss_ingest" in a for a in alerts))

    def test_stale_job_alert(self):
        from qa.management.commands.check_alerts import collect_alerts

        JobRun.objects.create(
            key="lotto_sync",
            status="success",
            last_success_at=timezone.now() - timedelta(hours=50),
        )
        alerts = collect_alerts()
        self.assertTrue(any("stale" in a for a in alerts))

    def test_5xx_spike_alert(self):
        from qa import metrics
        from qa.management.commands.check_alerts import collect_alerts

        metrics.incr("server_errors_total", "home:index", 25)
        alerts = collect_alerts()
        self.assertTrue(any("5xx" in a for a in alerts))

    def test_command_exit_codes(self):
        from django.core.management import call_command

        call_command("check_alerts")  # healthy -> exit 0
        JobRun.objects.create(
            key="rss_ingest", status="failed",
            last_run_at=timezone.now(), last_error="x",
        )
        with self.assertRaises(SystemExit) as ctx:
            call_command("check_alerts", fail=True)
        self.assertEqual(ctx.exception.code, 1)


class BackupRestoreTests(TestCase):
    """Task 25: backup/restore drill ด้วยไฟล์ชั่วคราว."""

    def test_backup_restore_roundtrip(self):
        import pathlib
        import tempfile

        from qa.backup import backup_sqlite, prune_backups, restore_sqlite

        with tempfile.TemporaryDirectory() as tmp:
            dest = backup_sqlite(dest_dir=tmp, keep=7)
            self.assertTrue(dest.exists())
            self.assertTrue((dest.parent / (dest.name + ".sha256")).exists())

            scratch = str(pathlib.Path(tmp) / "restored.sqlite3")
            tables = restore_sqlite(dest, target=scratch)
            self.assertGreater(tables, 0)

            for _ in range(3):
                backup_sqlite(dest_dir=tmp, keep=2)
            remaining = list(pathlib.Path(tmp).glob("*.sqlite3.gz"))
            self.assertLessEqual(len(remaining), 2)
            prune_backups(tmp, keep=7)

    def test_backup_command(self):
        import tempfile

        from django.core.management import call_command
        from django.test import override_settings

        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(BACKUP_DIR=tmp):
                call_command("backup_db")
            import pathlib

            self.assertEqual(len(list(pathlib.Path(tmp).glob("*.sqlite3.gz"))), 1)

    def test_restore_requires_confirm(self):
        from django.core.management import call_command

        with self.assertRaises(Exception):
            call_command("restore_db", file_="x.gz")
