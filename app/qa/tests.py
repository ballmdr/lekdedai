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
