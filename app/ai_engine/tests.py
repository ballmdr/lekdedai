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
