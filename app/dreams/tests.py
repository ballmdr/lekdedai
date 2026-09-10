import json
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

# Create your tests here.


class DreamPrivacyTests(TestCase):
    """Task 7: ไม่เก็บ IP, มี notice, retention ทำงาน."""

    def test_analyze_stores_no_ip(self):
        from dreams.models import DreamInterpretation

        res = self.client.post(
            "/dreams/analyze/",
            data=json.dumps({"dream_text": "ฝันเห็นงูใหญ่"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        row = DreamInterpretation.objects.get()
        self.assertIsNone(row.ip_address)
        self.assertEqual(row.dream_text, "ฝันเห็นงูใหญ่")

    def test_form_shows_privacy_notice(self):
        res = self.client.get("/dreams/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "ไม่เก็บ IP")
        self.assertContains(res, "เพื่อความบันเทิง")

    def test_cleanup_deletes_old_and_nulls_ip(self):
        from django.core.management import call_command

        from dreams.models import DreamInterpretation

        old = DreamInterpretation.objects.create(
            dream_text="เก่า", ip_address="1.2.3.4"
        )
        DreamInterpretation.objects.filter(pk=old.pk).update(
            interpreted_at=timezone.now() - timedelta(days=100)
        )
        new = DreamInterpretation.objects.create(dream_text="ใหม่")
        call_command("cleanup_old_dreams", days=90)
        self.assertFalse(DreamInterpretation.objects.filter(pk=old.pk).exists())
        new.refresh_from_db()
        self.assertIsNone(new.ip_address)


class DreamToNotebookTests(TestCase):
    """Task 10: ผลฝันเลือกบันทึกทีละเลขได้ + input ผิดรูปไม่ล่ม."""

    def _make_keyword(self):
        from dreams.models import DreamCategory, DreamKeyword

        cat = DreamCategory.objects.create(name="สัตว์", description="x")
        DreamKeyword.objects.create(
            keyword="งู", category=cat,
            main_number="8", secondary_number="9", common_numbers="89,98",
        )

    def test_analyze_returns_selectable_numbers(self):
        self._make_keyword()
        res = self.client.post(
            "/dreams/analyze/",
            data=json.dumps({"dream_text": "ฝันเห็นงูใหญ่"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()["result"]
        self.assertIn("89", data["numbers"])
        self.assertIn("งู", data["keywords"])

    def test_analyze_empty_text_400(self):
        res = self.client.post(
            "/dreams/analyze/",
            data=json.dumps({"dream_text": "   "}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

    def test_analyze_long_text_no_crash(self):
        res = self.client.post(
            "/dreams/analyze/",
            data=json.dumps({"dream_text": "ฝันเห็นงู " * 500}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)

    def test_notebook_prefill_handoff(self):
        res = self.client.get("/notebook/?number=89&source=dream&reason=test")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'id="nbNumber"')
