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


class AiCardConsistencyTests(TestCase):
    """การ์ด AI ต้องไม่โชว์คะแนนลอย ๆ โดยไม่มีเลข."""

    def _make_prediction(self, three_digit, confidence=68.0):
        from ai_engine.models import LuckyNumberPrediction

        return LuckyNumberPrediction.objects.create(
            two_digit_numbers="10,20",
            three_digit_numbers=three_digit,
            overall_confidence=confidence,
        )

    def test_ai_card_without_number_hides_confidence(self):
        self._make_prediction("")
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.context["ai_card"]["has_number"])
        self.assertNotContains(res, "68 คะแนน")

    def test_ai_card_normalizes_legacy_confidence(self):
        self._make_prediction("110", confidence=68.0)
        res = self.client.get("/")
        card = res.context["ai_card"]
        self.assertTrue(card["has_number"])
        self.assertEqual(card["number"], "110")
        self.assertEqual(card["confidence"], 68)


class ThaiDateTests(TestCase):
    def test_thai_date_formats_buddhist_year(self):
        from datetime import date

        from utils.thai_date import format_thai_date

        self.assertEqual(format_thai_date(date(2026, 9, 1)), "1 กันยายน 2569")


class Task12UxTests(TestCase):
    """Task 12: formatter ฝันตัวเดียว, heading ไม่ข้ามขั้น, ไม่มี alert บล็อกจอ."""

    def test_shared_formatter_used_by_both_dream_uis(self):
        import pathlib

        self.assertTrue(pathlib.Path("app/static/js/format.js").exists())
        home = self.client.get("/").content.decode()
        dream = self.client.get("/dreams/").content.decode()
        self.assertIn("js/format.js", home)
        self.assertIn("js/format.js", dream)
        self.assertNotIn("function formatInterpretation", home)
        self.assertNotIn("function formatInterpretation", dream)

    def test_homepage_heading_order(self):
        import re

        html = self.client.get("/").content.decode()
        levels = [int(m) for m in re.findall(r"<h([1-6])[\s>]", html)]
        self.assertGreaterEqual(len(levels), 2)
        self.assertEqual(levels[0], 1)
        self.assertEqual(levels.count(1), 1)
        for prev, cur in zip(levels, levels[1:]):
            self.assertLessEqual(cur, prev + 1, f"heading ข้ามขั้น: h{prev} -> h{cur}")

    def test_no_blocking_alerts_in_home_and_dream(self):
        home = self.client.get("/").content.decode()
        dream = self.client.get("/dreams/").content.decode()
        self.assertNotIn("alert(", home)
        self.assertNotIn("alert(", dream)

    def test_inline_error_elements_exist(self):
        home = self.client.get("/").content.decode()
        dream = self.client.get("/dreams/").content.decode()
        self.assertIn('id="dreamError"', home)
        self.assertIn('id="lotteryError"', home)
        self.assertIn('id="dreamSubmitError"', dream)
