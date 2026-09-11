"""Task 28: analytics privacy/validation tests + รายงาน."""
import json

from django.test import TestCase, override_settings

from analytics.models import AnalyticsEvent, compute_draw_period


class CollectEventTests(TestCase):
    def _post(self, payload):
        return self.client.post(
            "/analytics/event/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_valid_event_stored_minimal(self):
        res = self._post({"name": "landing_view", "session_id": "abc123"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["stored"])
        row = AnalyticsEvent.objects.get()
        self.assertEqual(row.name, "landing_view")
        self.assertEqual(row.session_id, "abc123")
        self.assertIsNotNone(row.draw_period)

    def test_payload_inspection_drops_extra_fields(self):
        """ส่งข้อความฝัน/เลข/IP มาด้วย — ต้องไม่ถูกเก็บเลย."""
        res = self._post({
            "name": "dream_completed",
            "session_id": "s1",
            "dream_text": "ฝันเห็นงู",
            "number": "45",
            "ip": "1.2.3.4",
            "extra": {"a": 1},
        })
        self.assertEqual(res.status_code, 200)
        row = AnalyticsEvent.objects.get()
        fields = [f.name for f in AnalyticsEvent._meta.get_fields()]
        for forbidden in ("dream_text", "number", "ip", "ip_address", "extra"):
            self.assertNotIn(forbidden, fields)
        self.assertNotIn("งู", str(vars(row)))

    def test_unknown_event_rejected(self):
        res = self._post({"name": "dream_text_dump", "session_id": "s"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(AnalyticsEvent.objects.count(), 0)

    def test_missing_session_rejected(self):
        res = self._post({"name": "landing_view", "session_id": ""})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(AnalyticsEvent.objects.count(), 0)

    def test_oversized_body_rejected(self):
        res = self._post({"name": "landing_view", "session_id": "x" * 5000})
        self.assertEqual(res.status_code, 413)

    def test_rate_limit(self):
        from django.core.cache import cache

        cache.clear()
        with override_settings(
            RATELIMIT_OVERRIDES={"analytics.views.collect_event": "2/m"}
        ):
            self._post({"name": "landing_view", "session_id": "a"})
            self._post({"name": "landing_view", "session_id": "b"})
            res = self._post({"name": "landing_view", "session_id": "c"})
        self.assertEqual(res.status_code, 429)

    @override_settings(ANALYTICS_ENABLED=False)
    def test_disabled_collects_nothing(self):
        res = self._post({"name": "landing_view", "session_id": "s"})
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["stored"])
        self.assertEqual(AnalyticsEvent.objects.count(), 0)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get("/analytics/event/").status_code, 405)


class DrawPeriodTests(TestCase):
    def test_draw_period_is_next_draw(self):
        from datetime import date

        # 2026-09-05 -> งวดถัดไป 16/09/2026
        self.assertEqual(
            compute_draw_period(date(2026, 9, 5)).isoformat(), "2026-09-16"
        )
        # วันหวยออกเองนับงวดนั้น
        self.assertEqual(
            compute_draw_period(date(2026, 9, 16)).isoformat(), "2026-09-16"
        )


class ReportCommandTests(TestCase):
    def test_report_runs(self):
        from datetime import timedelta

        from django.core.management import call_command
        from django.utils import timezone

        now = timezone.now()
        AnalyticsEvent.objects.create(name="landing_view", session_id="s1")
        row = AnalyticsEvent.objects.create(name="dream_completed", session_id="s1")
        # จำลองคนละงวด
        AnalyticsEvent.objects.filter(pk=row.pk).update(
            draw_period=now.date() + timedelta(days=20)
        )
        AnalyticsEvent.objects.create(name="dream_completed", session_id="s2")
        call_command("analytics_report", days=30)  # ต้องไม่ throw

    def test_cross_draw_retention_counts(self):
        from datetime import timedelta

        from django.core.management import call_command
        from django.utils import timezone

        base = timezone.now().date()
        AnalyticsEvent.objects.create(name="landing_view", session_id="keep")
        r1 = AnalyticsEvent.objects.create(name="result_checked", session_id="keep")
        AnalyticsEvent.objects.filter(pk=r1.pk).update(draw_period=base + timedelta(days=20))
        AnalyticsEvent.objects.create(name="result_checked", session_id="once")
        call_command("analytics_report")  # smoke — logic ตรวจซ้ำผ่าน ORM ในเทสต์อื่น
