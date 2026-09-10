"""Tests สำหรับหน้าหลัก (simplified): empty-state honesty, routing, error pages."""
import json

from django.test import TestCase, override_settings

from home.views import get_next_draw_prediction


class HomePageTests(TestCase):
    def test_home_renders(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)

    def test_no_fake_fallback_numbers(self):
        """Task 5/11 regression: ห้ามมีเลขตัวอย่าง 47/23/89/15/72/34 ในหน้าแรก."""
        res = self.client.get("/")
        for number in ["47", "23", "89", "15", "72", "34"]:
            self.assertNotContains(res, f">{number}</div>")

    def test_empty_state_is_honest(self):
        res = self.client.get("/")
        self.assertContains(res, "ยังไม่มีเลขแนะนำ")
        self.assertContains(res, "ยังไม่มีข้อมูลสถิติ")

    def test_target_draw_date_is_shown(self):
        res = self.client.get("/")
        self.assertContains(res, "งวดวันที่")

    def test_prediction_numbers_use_ranking_scores(self):
        result = get_next_draw_prediction()
        for item in result["prediction_numbers"]:
            self.assertIn("score", item)
            self.assertNotIn("confidence", item)

    def test_prediction_summary_is_honest_when_empty(self):
        result = get_next_draw_prediction()
        if not result["prediction_numbers"]:
            self.assertFalse(result["has_data"])
            self.assertIn("ยังไม่มีข้อมูล", result["data_source_summary"])

    def test_daily_numbers_status_api_shape(self):
        res = self.client.get("/api/daily-numbers-status/")
        self.assertEqual(res.status_code, 200)
        body = json.loads(res.content)
        self.assertTrue(body["success"])
        self.assertIn("status", body["data"])


class ErrorPageTests(TestCase):
    """หน้า 404/500 ต้องมี branding และทางกลับ ไม่ใช่หน้า Django เปล่า."""

    @override_settings(DEBUG=False)
    def test_404_has_branding_and_links(self):
        res = self.client.get("/definitely-not-a-real-page/")
        self.assertEqual(res.status_code, 404)
        self.assertContains(res, "ไม่พบหน้าที่คุณกำลังมองหา", status_code=404)
        self.assertContains(res, 'href="/"', status_code=404)
