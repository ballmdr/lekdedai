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

    def test_default_draw_is_next_draw(self):
        """ค่าเริ่มต้นต้องเป็นงวดถัดไป ไม่ใช่รางวัลเก่า (กันผู้ใช้บันทึกผิดงวด)."""
        from utils.lottery_dates import LOTTERY_DATES

        res = self.client.get("/notebook/")
        self.assertEqual(res.context["default_draw"], LOTTERY_DATES.get_next_draw_date())
        self.assertContains(res, LOTTERY_DATES.get_next_draw_date())


class NotebookHistoryUiTests(TestCase):
    """Task 11: หน้าประวัติต้องมีปุ่มตรวจ ที่มา/เหตุผล/งวด/ผลในแถวเดียว."""

    def test_history_ui_present(self):
        res = self.client.get("/notebook/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "nbCheckAll")
        self.assertContains(res, "ตรวจผลทั้งหมด")
        self.assertContains(res, "/lottery_checker/api/check-draw/")
        self.assertContains(res, "csrfmiddlewaretoken")
