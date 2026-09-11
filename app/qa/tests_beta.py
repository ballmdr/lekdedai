"""Task 30/31: ประตูปิด beta, feedback, รายงาน beta และ staged rollout/smoke."""
import json
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from qa.models import BetaInvite, JobRun, SystemFlag
from qa.rollout import BETA_ACCESS_SESSION_KEY, compute_beta_status, redeem_beta_code

User = get_user_model()


class BetaGateTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_gate_closed_by_default(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    @override_settings(BETA_MODE=True, BETA_INVITE_CODES=[])
    def test_beta_mode_redirects_stranger(self):
        res = self.client.get("/", HTTP_HOST="localhost")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/beta/", res["Location"])

    @override_settings(BETA_MODE=True, BETA_INVITE_CODES=[])
    def test_exempt_paths_still_open(self):
        self.assertEqual(
            self.client.get("/health/", HTTP_HOST="localhost").status_code, 200
        )
        self.assertEqual(
            self.client.get("/contact/", HTTP_HOST="localhost").status_code, 200
        )
        self.assertEqual(
            self.client.get("/privacy/", HTTP_HOST="localhost").status_code, 200
        )

    @override_settings(BETA_MODE=True, BETA_INVITE_CODES=["letmein"])
    def test_redeem_code_grants_access_and_records(self):
        res = self.client.post(
            "/beta/", {"code": "letmein"}, HTTP_HOST="localhost"
        )
        self.assertEqual(res.status_code, 302)
        self.assertTrue(self.client.session.get(BETA_ACCESS_SESSION_KEY))
        invite = BetaInvite.objects.get(code="letmein")
        self.assertEqual(invite.used_count, 1)
        self.assertIsNotNone(invite.last_used_at)
        self.assertEqual(self.client.get("/", HTTP_HOST="localhost").status_code, 200)

    @override_settings(BETA_MODE=True, BETA_INVITE_CODES=["letmein"])
    def test_invalid_code_rejected(self):
        res = self.client.post("/beta/", {"code": "nope"}, HTTP_HOST="localhost")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "รหัสเชิญไม่ถูกต้อง")
        self.assertFalse(self.client.session.get(BETA_ACCESS_SESSION_KEY))
        self.assertEqual(BetaInvite.objects.count(), 0)

    @override_settings(BETA_MODE=True, BETA_INVITE_CODES=[])
    def test_staff_bypasses_gate(self):
        staff = User.objects.create_user("staff", password="pw", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get("/", HTTP_HOST="localhost").status_code, 200)

    @override_settings(BETA_MODE=True, BETA_INVITE_CODES=[])
    def test_exhausted_invite_rejected(self):
        BetaInvite.objects.create(code="used", max_uses=1, used_count=1)
        self.assertIsNone(redeem_beta_code("used"))
        self.assertFalse(self.client.session.get(BETA_ACCESS_SESSION_KEY))

    @override_settings(BETA_MODE=True, BETA_INVITE_CODES=[])
    def test_inactive_invite_rejected(self):
        BetaInvite.objects.create(code="old", is_active=False)
        self.assertIsNone(redeem_beta_code("old"))

    @override_settings(BETA_MODE=True, BETA_INVITE_CODES=["cap"])
    def test_invite_capacity_limit(self):
        invite = BetaInvite.objects.create(code="cap", max_uses=2)
        self.assertIsNotNone(redeem_beta_code("cap"))
        self.assertIsNotNone(redeem_beta_code("cap"))
        self.assertIsNone(redeem_beta_code("cap"))
        invite.refresh_from_db()
        self.assertEqual(invite.used_count, 2)

    def test_unknown_code_returns_none(self):
        self.assertIsNone(redeem_beta_code("no-such-code"))


class RolloutStageTests(TestCase):
    def setUp(self):
        cache.clear()

    @override_settings(ROLLOUT_STAGE="pct10", ROLLOUT_PERCENT=100)
    def test_pct100_allows_all(self):
        self.assertEqual(self.client.get("/", HTTP_HOST="localhost").status_code, 200)

    @override_settings(ROLLOUT_STAGE="pct10", ROLLOUT_PERCENT=0)
    def test_pct0_blocks_all(self):
        res = self.client.get("/", HTTP_HOST="localhost")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/beta/", res["Location"])

    @override_settings(ROLLOUT_STAGE="bogus")
    def test_invalid_stage_falls_back_public(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    @override_settings(ROLLOUT_KILL_SWITCH=True)
    def test_kill_switch_closes_for_public(self):
        res = self.client.get("/", HTTP_HOST="localhost")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/beta/closed/", res["Location"])
        closed = self.client.get("/beta/closed/", HTTP_HOST="localhost")
        self.assertEqual(closed.status_code, 200)
        self.assertContains(closed, "ระบบปิดชั่วคราว")

    @override_settings(ROLLOUT_KILL_SWITCH=True)
    def test_kill_switch_staff_still_browses(self):
        staff = User.objects.create_user("ops", password="pw", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get("/", HTTP_HOST="localhost").status_code, 200)


class StopCriteriaTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_open_when_healthy(self):
        status = compute_beta_status()
        self.assertEqual(status["state"], "open")

    def test_paused_on_failed_job(self):
        JobRun.objects.create(key="rss_ingest", status="failed", last_error="boom")
        status = compute_beta_status()
        self.assertEqual(status["state"], "paused")
        self.assertTrue(any("rss_ingest" in r for r in status["reasons"]))

    def test_closed_on_p0_flag(self):
        SystemFlag.objects.create(key="lottery-wrong", level="P0", message="ผลหวยผิด")
        status = compute_beta_status()
        self.assertEqual(status["state"], "closed")

    @override_settings(BETA_MODE=True, BETA_INVITE_CODES=[])
    def test_p0_flag_blocks_non_staff(self):
        SystemFlag.objects.create(key="leak", level="P0", message="ข้อมูลรั่ว")
        res = self.client.get("/", HTTP_HOST="localhost")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/beta/closed/", res["Location"])

    @override_settings(BETA_MODE=True, BETA_INVITE_CODES=[])
    def test_p1_flag_does_not_close(self):
        SystemFlag.objects.create(key="warn", level="P1", message="ช้า")
        status = compute_beta_status()
        self.assertEqual(status["state"], "open")

    @override_settings(BETA_MODE=True, BETA_INVITE_CODES=["ok"])
    def test_paused_still_allows_redeemed_user(self):
        JobRun.objects.create(key="rss_ingest", status="failed", last_error="x")
        self.client.post("/beta/", {"code": "ok"}, HTTP_HOST="localhost")
        self.assertEqual(self.client.get("/", HTTP_HOST="localhost").status_code, 200)


class BetaFeedbackTests(TestCase):
    def test_beta_feedback_stored(self):
        res = self.client.post(
            "/contact/",
            {"message_type": "beta", "name": "ผู้ใช้", "message": "อยากให้มี export"},
            HTTP_HOST="localhost",
        )
        self.assertEqual(res.status_code, 302)
        from home.models import ContactMessage

        row = ContactMessage.objects.get()
        self.assertEqual(row.message_type, "beta")

    def test_beta_type_preselect(self):
        res = self.client.get("/contact/?type=beta", HTTP_HOST="localhost")
        self.assertContains(res, 'value="beta" selected')

    def test_invalid_type_falls_back(self):
        from home.models import ContactMessage

        self.client.post(
            "/contact/",
            {"message_type": "hack", "message": "hi"},
            HTTP_HOST="localhost",
        )
        self.assertEqual(ContactMessage.objects.get().message_type, "contact")


class BetaReportTests(TestCase):
    def _seed(self):
        from analytics.models import AnalyticsEvent

        now = timezone.now()
        AnalyticsEvent.objects.create(name="landing_view", session_id="s1")
        AnalyticsEvent.objects.create(name="dream_started", session_id="s1")
        AnalyticsEvent.objects.create(name="dream_completed", session_id="s1")
        AnalyticsEvent.objects.create(name="number_saved", session_id="s1")
        r = AnalyticsEvent.objects.create(name="result_checked", session_id="s1")
        AnalyticsEvent.objects.filter(pk=r.pk).update(
            draw_period=now.date() + timedelta(days=20)
        )
        AnalyticsEvent.objects.create(name="landing_view", session_id="s2")
        AnalyticsEvent.objects.create(name="number_saved", session_id="s2")
        BetaInvite.objects.create(code="a", used_count=1)
        from home.models import ContactMessage

        ContactMessage.objects.create(message_type="beta", message="feedback")

    def test_report_runs_text(self):
        from io import StringIO

        from django.core.management import call_command

        self._seed()
        out = StringIO()
        call_command("beta_report", draws=2, stdout=out)
        text = out.getvalue()
        self.assertIn("Checkpoint E", text)
        self.assertIn("Feedback", text)
        self.assertIn("สถานะระบบ", text)

    def test_report_writes_json_file(self):
        from django.core.management import call_command

        self._seed()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "beta.json"
            call_command("beta_report", output=str(dest), format="json")
            data = json.loads(dest.read_text(encoding="utf-8"))
        self.assertIn("draws", data)
        self.assertIn("checkpoint_e", data)
        self.assertIn("system_status", data)

    def test_checkpoint_flags_two_draws_required(self):
        from django.core.management import call_command

        self._seed()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "beta.json"
            call_command("beta_report", output=str(dest), format="json")
            data = json.loads(dest.read_text(encoding="utf-8"))
        self.assertEqual(data["checkpoint_e"]["draws_with_data"], 2)
        self.assertTrue(data["checkpoint_e"]["has_two_draws"])


class AnalyticsReportOutputTests(TestCase):
    def test_output_text_and_json(self):
        from django.core.management import call_command
        from analytics.models import AnalyticsEvent

        cache.clear()  # กัน cache ข้าม test
        AnalyticsEvent.objects.create(name="landing_view", session_id="s1")
        with tempfile.TemporaryDirectory() as tmp:
            txt = Path(tmp) / "r.txt"
            call_command("analytics_report", output=str(txt))
            self.assertIn("Funnel", txt.read_text(encoding="utf-8"))
            js = Path(tmp) / "r.json"
            call_command("analytics_report", output=str(js), format="json")
            self.assertIn("funnel", json.loads(js.read_text(encoding="utf-8")))


class CsrfCookieTests(TestCase):
    """Task 30: analytics ต้องมี csrftoken cookie ทุกหน้า ไม่งั้น POST โดน 403."""

    def test_get_page_sets_csrf_cookie(self):
        res = self.client.get("/")
        self.assertIn("csrftoken", res.cookies)

    def test_analytics_post_with_csrf_cookie(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        page = client.get("/")
        token = page.cookies["csrftoken"].value
        res = client.post(
            "/analytics/event/",
            data=json.dumps({"name": "landing_view", "session_id": "abc"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["stored"])


class ProductionSmokeTests(TestCase):
    def test_db_issue_when_no_result(self):
        from qa.management.commands.production_smoke import collect_db_issues

        issues = collect_db_issues()
        self.assertTrue(any("ไม่มีผลหวย" in i for i in issues))

    def test_db_ok_with_recent_result(self):
        from lottery_checker.models import LottoResult
        from qa.management.commands.production_smoke import collect_db_issues

        LottoResult.objects.create(
            draw_date=timezone.localdate(), result_data={}, is_valid=True
        )
        self.assertEqual(collect_db_issues(), [])

    def test_db_issue_when_stale(self):
        from lottery_checker.models import LottoResult
        from qa.management.commands.production_smoke import collect_db_issues

        LottoResult.objects.create(
            draw_date=timezone.localdate() - timedelta(days=30),
            result_data={}, is_valid=True,
        )
        issues = collect_db_issues(max_stale_days=5)
        self.assertTrue(any("เก่า" in i for i in issues))

    def test_http_checks_collect_failures(self):
        from qa.management.commands.production_smoke import (
            SMOKE_ROUTES,
            collect_http_issues,
        )

        class Resp:
            def __init__(self, status_code):
                self.status_code = status_code

            def json(self):
                return {"status": "ok"}

        def fake_get(url, timeout=None):
            return Resp(500 if url.endswith("/news/") else 200)

        with patch(
            "qa.management.commands.production_smoke.requests.get",
            side_effect=fake_get,
        ):
            issues = collect_http_issues("https://example.com")

        self.assertTrue(any("/news/" in i for i in issues))
        self.assertEqual(len(issues), 1)
        self.assertIn("/news/", " ".join(SMOKE_ROUTES))

    def test_http_checks_all_ok(self):
        from qa.management.commands.production_smoke import collect_http_issues

        class Resp:
            status_code = 200

            def json(self):
                return {"status": "ok"}

        with patch(
            "qa.management.commands.production_smoke.requests.get",
            return_value=Resp(),
        ):
            self.assertEqual(collect_http_issues("https://example.com"), [])
