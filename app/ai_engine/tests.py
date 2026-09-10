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
