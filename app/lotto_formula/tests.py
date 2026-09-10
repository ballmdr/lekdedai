"""Regression tests: หน้าเครื่องคำนวณต้องใช้งานได้จริง ไม่ใช่ placeholder."""
import json

from django.test import TestCase

from .models import LotteryFormula


class CalculatorPageTests(TestCase):
    def test_home_renders_without_formulas(self):
        res = self.client.get("/lotto_formula/")
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, "Hero Section")
        self.assertContains(res, "ยังไม่มีสูตร")

    def test_calculator_renders_without_formulas(self):
        res = self.client.get("/lotto_formula/calculator/")
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, "React Calculator Component")
        self.assertContains(res, "ยังไม่มีสูตร")

    def test_calculator_has_csrf_token_when_formulas_exist(self):
        LotteryFormula.objects.create(
            name="สูตรทดสอบ",
            description="d",
            method="m",
            accuracy_rate=0,
        )
        res = self.client.get("/lotto_formula/calculator/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "csrfmiddlewaretoken")


class CalculateApiTests(TestCase):
    def setUp(self):
        self.formula = LotteryFormula.objects.create(
            name="สูตรบวกลบ",
            description="d",
            method="m",
            accuracy_rate=0,
        )

    def _post(self, payload):
        return self.client.post(
            "/lotto_formula/api/calculate/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_missing_input_returns_json_400(self):
        res = self._post({"formula_id": self.formula.id, "input_numbers": ""})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()["success"])

    def test_unknown_formula_returns_json_404(self):
        res = self._post({"formula_id": 999999, "input_numbers": "12"})
        self.assertEqual(res.status_code, 404)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertIn("ไม่พบสูตร", body["error"])

    def test_insufficient_digits_returns_json_400(self):
        res = self._post({"formula_id": self.formula.id, "input_numbers": "5"})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()["success"])

    def test_valid_calculation(self):
        res = self._post({"formula_id": self.formula.id, "input_numbers": "123456"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(len(body["calculated_numbers"]), 3)
        self.assertNotEqual(body["calculated_numbers"], ["000", "111", "222"])
