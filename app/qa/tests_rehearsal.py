"""Task 29: dress rehearsal — happy path + fault injection ครบ + cleanup."""
from django.test import TestCase


class RehearsalTests(TestCase):
    def setUp(self):
        from lotto_formula.models import LotteryFormula

        LotteryFormula.objects.create(
            code="sum_diff", name="สูตรบวกลบ", description="d", method="m",
            accuracy_rate=0, is_approved=True,
        )

    def _run(self):
        from qa.rehearsal import run_rehearsal

        return run_rehearsal(cleanup=True)

    def test_rehearsal_all_steps_pass(self):
        report = self._run()
        statuses = {s["name"]: s["status"] for s in report["steps"]}
        self.assertNotIn("fail", set(statuses.values()), statuses)
        self.assertEqual(report["overall"], "pass", report["steps"])

    def test_required_steps_present(self):
        report = self._run()
        names = {s["name"] for s in report["steps"]}
        for required in (
            "health_baseline",
            "news_happy_path",
            "empty_news_no_crash",
            "ai_failure_keeps_data",
            "upstream_down_safe",
            "prediction_and_result_cycle",
            "user_result_check",
            "analytics_event",
            "backup_restore_drill",
            "stale_data_degraded",
            "failure_alerts",
            "cleanup",
        ):
            self.assertIn(required, names)

    def test_report_is_signed(self):
        report = self._run()
        self.assertIn("report_sha256", report)
        self.assertEqual(len(report["report_sha256"]), 64)
        self.assertIn("git_rev", report)
        self.assertIsNotNone(report["started_at"])

    def test_cleanup_removes_rehearsal_data(self):
        from ai_engine.models import DataSource
        from analytics.models import AnalyticsEvent
        from news.models import NewsArticle

        self._run()
        self.assertEqual(DataSource.objects.filter(key="rehearsal-source").count(), 0)
        self.assertEqual(
            NewsArticle.objects.filter(data_source__key="rehearsal-source").count(), 0
        )
        self.assertEqual(
            AnalyticsEvent.objects.filter(session_id__startswith="rehearsal-").count(),
            0,
        )

    def test_command_writes_report_file(self):
        import json
        import tempfile
        from pathlib import Path

        from django.core.management import call_command

        with tempfile.TemporaryDirectory() as tmp:
            call_command("rehearsal_check", report_dir=tmp)
            files = list(Path(tmp).glob("rehearsal-*.json"))
            self.assertEqual(len(files), 1)
            data = json.loads(files[0].read_text(encoding="utf-8"))
            self.assertIn("steps", data)
            self.assertIn("report_sha256", data)
