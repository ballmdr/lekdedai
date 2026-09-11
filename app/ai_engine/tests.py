from django.contrib.auth import get_user_model
from django.test import TestCase

# Create your tests here.


class AiEngineSecurityTests(TestCase):
    """Task 4: ingestion endpoints ต้องเป็น staff เท่านั้น."""

    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user("staff", password="pw", is_staff=True)
        self.user = User.objects.create_user("plain", password="pw")

    def test_refresh_data_sources_anonymous_forbidden(self):
        res = self.client.post("/ai/api/refresh-data-sources/")
        self.assertEqual(res.status_code, 403)

    def test_refresh_data_sources_non_staff_forbidden(self):
        self.client.force_login(self.user)
        res = self.client.post("/ai/api/refresh-data-sources/")
        self.assertEqual(res.status_code, 403)

    def test_trigger_collection_anonymous_forbidden(self):
        res = self.client.post("/ai/api/data-source/999/collect/")
        self.assertEqual(res.status_code, 403)

    def test_trigger_collection_get_not_allowed(self):
        self.client.force_login(self.staff)
        res = self.client.get("/ai/api/data-source/999/collect/")
        self.assertEqual(res.status_code, 405)


class AiPageRouteTests(TestCase):
    """Regression: /ai/history/ และ /ai/accuracy/ ต้องไม่ 500 อีก."""

    def test_history_renders(self):
        res = self.client.get("/ai/history/")
        self.assertEqual(res.status_code, 200)

    def test_accuracy_renders_with_empty_state(self):
        res = self.client.get("/ai/accuracy/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "ยังไม่มีข้อมูลความแม่นยำ")


class SourceRegistryTests(TestCase):
    """Task 16: ทะเบียนแหล่งข่าว version-controlled, seed idempotent."""

    def _seed(self):
        from django.core.management import call_command

        call_command("setup_ai_data_sources", create_sources=True)

    def test_seed_matches_registry_file(self):
        from ai_engine.models import DataSource
        from ai_engine.source_registry import SOURCE_REGISTRY

        self._seed()
        rows = {
            s.key: s for s in DataSource.objects.filter(key__isnull=False)
        }
        self.assertEqual(set(rows), {e["key"] for e in SOURCE_REGISTRY})
        for entry in SOURCE_REGISTRY:
            row = rows[entry["key"]]
            self.assertEqual(row.url, entry["url"])
            self.assertEqual(row.category, entry["category"])
            self.assertEqual(row.is_active, entry["is_active"])
            self.assertEqual(row.attribution, entry["attribution"])
            self.assertEqual(row.scraping_interval, entry["scraping_interval"])

    def test_seed_idempotent_and_preserves_timestamps(self):
        from datetime import timedelta

        from django.utils import timezone

        from ai_engine.models import DataSource

        self._seed()
        before = sorted(
            (s.key, s.name, s.url, s.is_active) for s in DataSource.objects.all()
        )
        stamp = timezone.now() - timedelta(hours=5)
        DataSource.objects.filter(key="thairath-rss").update(
            last_success_at=stamp, last_failure_at=stamp
        )
        self._seed()
        after = sorted(
            (s.key, s.name, s.url, s.is_active) for s in DataSource.objects.all()
        )
        self.assertEqual(before, after)
        row = DataSource.objects.get(key="thairath-rss")
        self.assertEqual(row.last_success_at, stamp)
        self.assertEqual(row.last_failure_at, stamp)

    def test_deactivates_legacy_junk_but_keeps_custom_rows(self):
        from ai_engine.models import DataSource

        junk = DataSource.objects.create(
            name="Facebook - กลุมหวย", source_type="social_media",
            url="https://facebook.com", is_active=True,
        )
        custom = DataSource.objects.create(
            name="ของฉันเอง", source_type="news",
            url="https://example.com/feed", is_active=True,
        )
        self._seed()
        junk.refresh_from_db()
        custom.refresh_from_db()
        self.assertFalse(junk.is_active)
        self.assertTrue(custom.is_active)

    def test_data_sources_page_shows_registry(self):
        self._seed()
        res = self.client.get("/ai/data-sources/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "ไทยรัฐ RSS")
        self.assertContains(res, "INN News RSS")
        self.assertContains(res, "สำเร็จล่าสุด")
        self.assertContains(res, "ล้มเหลวล่าสุด")


def _make_ai_model(name="M", version="2.0"):
    from ai_engine.models import AIModel

    return AIModel.objects.create(
        name=name, version=version, algorithm="statistical"
    )


def _make_old_prediction(**kwargs):
    from datetime import timedelta

    from django.utils import timezone

    from ai_engine.models import LuckyNumberPrediction

    defaults = {
        "two_digit_numbers": "10,20",
        "three_digit_numbers": "110",
        "overall_confidence": 68.0,
        "for_draw_date": timezone.localdate() + timedelta(days=5),
        "ai_model": _make_ai_model(),
        "factors_used": {"date_pattern": {}, "historical_hot": {}},
    }
    defaults.update(kwargs)
    return LuckyNumberPrediction.objects.create(**defaults)


def _make_session(**kwargs):
    import uuid
    from datetime import timedelta

    from django.utils import timezone

    from ai_engine.models import PredictionSession

    now = timezone.now()
    defaults = {
        "session_id": f"s-{uuid.uuid4().hex[:12]}",
        "for_draw_date": timezone.localdate() + timedelta(days=5),
        "data_collection_period_start": now - timedelta(days=7),
        "data_collection_period_end": now,
        "status": "completed",
        "total_data_sources": 2,
        "total_data_points": 50,
    }
    defaults.update(kwargs)
    return PredictionSession.objects.create(**defaults)


def _make_ensemble(session=None, **kwargs):
    from ai_engine.models import EnsemblePrediction

    session = session or _make_session()
    defaults = {
        "session": session,
        "final_two_digit": [{"number": "10", "confidence": 0.85, "reasoning": "r"}],
        "final_three_digit": [{"number": "110", "confidence": 0.8, "reasoning": "r"}],
        "overall_confidence": 0.82,
        "prediction_summary": "สรุป",
        "model_contributions": {"Journalist AI": {"weight": 0.4}},
        "total_data_points": 50,
    }
    defaults.update(kwargs)
    return EnsemblePrediction.objects.create(**defaults)


class PredictionReadinessTests(TestCase):
    """Task 20: readiness gate ทั้งสองระบบ."""

    def test_old_ready_when_complete(self):
        row = _make_old_prediction()
        self.assertTrue(row.is_ready())
        self.assertEqual(row.readiness_status(), "ready")
        meta = row.readiness_meta()
        self.assertEqual(meta["confidence_percent"], 68)
        self.assertIn("M v2.0", meta["model_label"])

    def test_old_incomplete_without_model_or_draw_or_numbers(self):
        self.assertEqual(
            _make_old_prediction(ai_model=None).readiness_status(), "incomplete"
        )
        self.assertEqual(
            _make_old_prediction(for_draw_date=None).readiness_status(), "incomplete"
        )
        self.assertEqual(
            _make_old_prediction(three_digit_numbers="").readiness_status(),
            "incomplete",
        )

    def test_old_stale_when_draw_passed(self):
        from datetime import timedelta

        from django.utils import timezone

        row = _make_old_prediction(
            for_draw_date=timezone.localdate() - timedelta(days=2)
        )
        self.assertTrue(row.is_stale())
        self.assertEqual(row.readiness_status(), "stale")
        self.assertIsNone(row.readiness_meta()["confidence_percent"])

    def test_ensemble_ready_and_meta(self):
        row = _make_ensemble()
        self.assertTrue(row.is_ready())
        self.assertEqual(row.readiness_status(), "ready")
        meta = row.readiness_meta()
        self.assertEqual(meta["confidence_percent"], 82)
        self.assertIn("Journalist AI", meta["model_label"])
        self.assertIsNotNone(meta["data_window"])

    def test_ensemble_incomplete_cases(self):
        self.assertEqual(
            _make_ensemble(session=_make_session(status="failed")).readiness_status(),
            "incomplete",
        )
        self.assertEqual(
            _make_ensemble(total_data_points=0).readiness_status(), "incomplete"
        )
        self.assertEqual(
            _make_ensemble(final_two_digit=[], final_three_digit=[]).readiness_status(),
            "incomplete",
        )

    def test_ensemble_stale(self):
        from datetime import timedelta

        from django.utils import timezone

        row = _make_ensemble(
            session=_make_session(
                for_draw_date=timezone.localdate() - timedelta(days=2)
            )
        )
        self.assertEqual(row.readiness_status(), "stale")
        self.assertIsNone(row.readiness_meta()["confidence_percent"])

    def test_featured_gate_blocks_incomplete(self):
        row = _make_ensemble(
            session=_make_session(status="analyzing"), is_featured=True
        )
        row.refresh_from_db()
        self.assertFalse(row.is_featured)

    def test_featured_gate_keeps_ready(self):
        row = _make_ensemble(is_featured=True)
        row.refresh_from_db()
        self.assertTrue(row.is_featured)

    def test_meta_keys_match_across_systems(self):
        old_meta = _make_old_prediction().readiness_meta()
        new_meta = _make_ensemble().readiness_meta()
        self.assertEqual(set(old_meta), set(new_meta))


class AiReadinessViewTests(TestCase):
    """Task 20: หน้า AI แสดงเฉพาะที่พร้อม ไม่สร้างอัตโนมัติ."""

    def test_page_does_not_auto_create(self):
        from ai_engine.models import LuckyNumberPrediction

        res = self.client.get("/ai/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(LuckyNumberPrediction.objects.count(), 0)
        self.assertContains(res, "ยังไม่มีการทำนายที่พร้อมแสดง")

    def test_incomplete_prediction_hidden(self):
        _make_old_prediction(ai_model=None)
        res = self.client.get("/ai/")
        self.assertContains(res, "ยังไม่มีการทำนายที่พร้อมแสดง")
        self.assertNotContains(res, "วิเคราะห์โดย")

    def test_ready_prediction_shows_same_meta(self):
        _make_old_prediction()
        res = self.client.get("/ai/")
        self.assertContains(res, "M v2.0")
        self.assertContains(res, "68%")
        self.assertContains(res, "พร้อมใช้")

    def test_stale_hides_confidence(self):
        from datetime import timedelta

        from django.utils import timezone

        _make_old_prediction(for_draw_date=timezone.localdate() - timedelta(days=2))
        res = self.client.get("/ai/")
        self.assertContains(res, "งวดนี้ออกผลแล้ว")
        self.assertNotContains(res, "ความมั่นใจ AI")

    def test_ensemble_history_badges(self):
        _make_ensemble()
        _make_ensemble(session=_make_session(status="analyzing"))
        res = self.client.get("/ai/ensemble/history/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "พร้อมใช้")
        self.assertContains(res, "รอข้อมูล")
