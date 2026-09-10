"""Task 9: สมุดเลข browser-only — server ส่งงวดให้ผูก ที่เหลือเกิดใน browser."""
from django.test import TestCase


class NotebookPageTests(TestCase):
    def test_page_renders_with_draws_and_notice(self):
        res = self.client.get("/notebook/")
        self.assertEqual(res.status_code, 200)
        # งวดจริงจาก LOTTERY_DATES ฝังมาให้ผูก (24 งวด)
        self.assertContains(res, "lekdedai_notebook_v1")
        self.assertContains(res, "อุปกรณ์นี้เท่านั้น")
        self.assertContains(res, "/lottery_checker/")

    def test_draw_options_cover_latest_draw(self):
        from utils.lottery_dates import LOTTERY_DATES

        res = self.client.get("/notebook/")
        latest = LOTTERY_DATES.get_dropdown_options(limit=1)[0]["value"]
        self.assertContains(res, latest)
