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


class FormulaRegistrySeedTests(TestCase):
    """Task 14: seed สูตรต้อง idempotent, มี contract, ไม่มีข้อมูลปลอม."""

    def _seed(self):
        from django.core.management import call_command

        call_command("populate_lottery_data")

    def _snapshot(self):
        return sorted(
            (
                f.code,
                f.version,
                f.name,
                f.is_approved,
                f.accuracy_rate,
                f.total_predictions,
                f.correct_predictions,
            )
            for f in LotteryFormula.objects.all()
        )

    def test_seed_twice_keeps_same_formulas(self):
        self._seed()
        first = self._snapshot()
        self.assertEqual(len(first), 4)
        self._seed()
        self.assertEqual(self._snapshot(), first)

    def test_seed_creates_no_fake_results_or_predictions(self):
        from lotto_formula.models import LotteryResult, Prediction

        self._seed()
        self.assertEqual(LotteryResult.objects.count(), 0)
        self.assertEqual(Prediction.objects.count(), 0)
        for formula in LotteryFormula.objects.all():
            self.assertEqual(formula.accuracy_rate, 0)
            self.assertEqual(formula.total_predictions, 0)
            self.assertEqual(formula.correct_predictions, 0)

    def test_contract_fields_present(self):
        self._seed()
        codes = set()
        for formula in LotteryFormula.objects.all():
            self.assertTrue(formula.code)
            self.assertTrue(formula.version)
            self.assertTrue(formula.is_approved)
            self.assertIn("reference_digits", formula.input_spec)
            self.assertEqual(formula.output_spec.get("count"), 3)
            codes.add(formula.code)
        self.assertEqual(codes, {"sum_diff", "running", "reverse", "even_odd"})

    def test_seed_preserves_real_measurements(self):
        self._seed()
        formula = LotteryFormula.objects.get(code="sum_diff")
        formula.total_predictions = 10
        formula.correct_predictions = 3
        formula.accuracy_rate = 30.0
        formula.save()
        self._seed()
        formula.refresh_from_db()
        self.assertEqual(formula.total_predictions, 10)
        self.assertEqual(formula.accuracy_rate, 30.0)


class FormulaDispatchTests(TestCase):
    """Task 14: คำนวณต้อง dispatch ด้วย code ไม่ใช่ชื่อแสดงผล."""

    def test_dispatch_by_code_not_name(self):
        from lotto_formula.views import calculate_by_formula

        custom = LotteryFormula.objects.create(
            code="sum_diff", name="ชื่ออะไรก็ได้", description="d", method="m",
            accuracy_rate=0,
        )
        self.assertEqual(
            calculate_by_formula(custom, "123456"), ["392", "312", "631"]
        )

    def test_deterministic_same_input_same_output(self):
        from lotto_formula.views import calculate_by_formula

        formula = LotteryFormula.objects.create(
            code="running", name="x", description="d", method="m", accuracy_rate=0,
        )
        self.assertEqual(
            calculate_by_formula(formula, "123456"),
            calculate_by_formula(formula, "123456"),
        )

    def test_unknown_code_uses_default_math(self):
        from lotto_formula.views import calculate_by_formula

        formula = LotteryFormula.objects.create(
            code="mystery", name="x", description="d", method="m", accuracy_rate=0,
        )
        self.assertEqual(
            calculate_by_formula(formula, "123456"), ["006", "002", "042"]
        )

    def test_unapproved_formula_hidden(self):
        hidden = LotteryFormula.objects.create(
            code="sum_diff", name="สูตรลับ", description="d", method="m",
            accuracy_rate=0, is_approved=False,
        )
        res = self.client.get("/lotto_formula/calculator/")
        self.assertNotContains(res, "สูตรลับ")
        res = self.client.post(
            "/lotto_formula/api/calculate/",
            data=json.dumps({"formula_id": hidden.id, "input_numbers": "123456"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 404)


def _verify_draw_payload():
    def nums(*values):
        return {"number": [{"value": v} for v in values]}

    data = {
        "first": nums("417212"),
        "second": nums("111111"),
        "third": nums("222222"),
        "fourth": nums("333333"),
        "fifth": nums("444444"),
        "last3f": nums("417", "990"),
        "last3b": nums("212", "007"),
        "last2": nums("12", "00"),
        "near1": nums("417211"),
    }
    return {"response": {"result": {"data": data}}}


class FormulaDeterminismTests(TestCase):
    """Task 15: input เดิมต้องได้ output เดิมทุกสูตร."""

    EXPECTED = {
        "sum_diff": ["392", "312", "331"],
        "running": ["123", "456", "789"],
        "reverse": ["002", "000", "002"],
        "even_odd": ["213", "112", "211"],
    }

    def test_each_formula_deterministic(self):
        from lotto_formula.views import calculate_by_formula

        for code, expected in self.EXPECTED.items():
            formula = LotteryFormula.objects.create(
                code=code, name=code, description="d", method="m", accuracy_rate=0,
            )
            first = calculate_by_formula(formula, "12")
            self.assertEqual(first, expected)
            self.assertEqual(calculate_by_formula(formula, "12"), first)

    def test_insufficient_input_returns_none(self):
        from lotto_formula.views import calculate_by_formula

        formula = LotteryFormula.objects.create(
            code="sum_diff", name="x", description="d", method="m", accuracy_rate=0,
        )
        self.assertIsNone(calculate_by_formula(formula, "5"))
        self.assertIsNone(calculate_by_formula(formula, ""))


class SavePredictionApiTests(TestCase):
    """Task 15: บันทึกได้เฉพาะงวดหน้า และเลขต้องตรงที่สูตรคำนวณได้."""

    def setUp(self):
        from utils.lottery_dates import LotteryDates

        self.formula = LotteryFormula.objects.create(
            code="sum_diff", name="สูตรบวกลบ", description="d", method="m",
            accuracy_rate=0,
        )
        self.upcoming = LotteryDates.get_upcoming_draw_dates(2)

    def _save(self, payload):
        return self.client.post(
            "/lotto_formula/api/save-prediction/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_save_upcoming_draw_pending(self):
        from lotto_formula.models import Prediction

        res = self._save({
            "formula_id": self.formula.id,
            "input_numbers": "12",
            "draw_date": self.upcoming[0],
        })
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["predicted_numbers"], ["392", "312", "331"])
        self.assertEqual(body["status"], "pending")
        row = Prediction.objects.get(id=body["prediction_id"])
        self.assertIsNone(row.is_correct)
        self.assertEqual(row.input_numbers, "12")

    def test_save_duplicate_returns_existing(self):
        from lotto_formula.models import Prediction

        payload = {
            "formula_id": self.formula.id,
            "input_numbers": "12",
            "draw_date": self.upcoming[0],
        }
        first = self._save(payload).json()
        second = self._save(payload).json()
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(first["prediction_id"], second["prediction_id"])
        self.assertEqual(Prediction.objects.count(), 1)

    def test_reject_past_draw(self):
        from utils.lottery_dates import LotteryDates

        past = LotteryDates.get_recent_draw_dates(60)[-1]
        res = self._save({
            "formula_id": self.formula.id,
            "input_numbers": "12",
            "draw_date": past,
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("งวดนี้ออกผลแล้ว", res.json()["error"])

    def test_reject_non_draw_date(self):
        res = self._save({
            "formula_id": self.formula.id,
            "input_numbers": "12",
            "draw_date": "2026-09-02",
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("วันหวยออก", res.json()["error"])

    def test_reject_unapproved_formula(self):
        hidden = LotteryFormula.objects.create(
            code="running", name="x", description="d", method="m",
            accuracy_rate=0, is_approved=False,
        )
        res = self._save({
            "formula_id": hidden.id,
            "input_numbers": "12",
            "draw_date": self.upcoming[0],
        })
        self.assertEqual(res.status_code, 404)


class BacktestVerificationTests(TestCase):
    """Task 15: ตรวจย้อนหลังกับผลจริง — numerator/denominator/ช่วงวันที่."""

    def setUp(self):
        from datetime import date

        from lotto_formula.models import Prediction
        from lottery_checker.lotto_service import LottoService
        from lotto_stats.lotto_sync_service import LottoSyncService

        self.formula = LotteryFormula.objects.create(
            code="sum_diff", name="สูตรบวกลบ", description="d", method="m",
            accuracy_rate=0,
        )
        # ห่วงโซ่ canonical: GLO payload -> LottoResult -> LotteryDraw
        self.assertTrue(LottoService().save_to_database(
            _verify_draw_payload(), date(2026, 9, 1)))
        result = LottoSyncService().sync_specific_date(date(2026, 9, 1))
        self.assertTrue(result["success"])

        Prediction.objects.create(
            formula=self.formula, predicted_numbers="417,111",
            input_numbers="99", draw_date=date(2026, 9, 1),
        )
        Prediction.objects.create(
            formula=self.formula, predicted_numbers="001,002",
            input_numbers="98", draw_date=date(2026, 9, 1),
        )
        Prediction.objects.create(
            formula=self.formula, predicted_numbers="417,111",
            input_numbers="97", draw_date=date(2026, 5, 1),
        )

    def test_verify_marks_won_lost_and_skips_missing(self):
        from django.core.management import call_command

        from lotto_formula.models import Prediction

        call_command("verify_formula_predictions")
        rows = {p.input_numbers: p for p in Prediction.objects.all()}
        self.assertTrue(rows["99"].is_correct)  # 417 ตรงเลขหน้า 3 ตัว
        self.assertFalse(rows["98"].is_correct)
        self.assertIsNone(rows["97"].is_correct)  # ไม่มีผลงวดนั้น คงรอตรวจ
        self.assertIsNotNone(rows["99"].verified_at)

    def test_formula_counters_use_verified_only(self):
        from django.core.management import call_command

        call_command("verify_formula_predictions")
        self.formula.refresh_from_db()
        self.assertEqual(self.formula.verified_count, 2)
        self.assertEqual(self.formula.correct_predictions, 1)
        self.assertEqual(self.formula.accuracy_rate, 50.0)

    def test_api_stats_verified_only(self):
        from django.core.management import call_command

        call_command("verify_formula_predictions")
        body = self.client.get("/lotto_formula/api/stats/").json()
        self.assertEqual(body["verified_predictions"], 2)
        self.assertEqual(body["correct_predictions"], 1)
        self.assertEqual(body["accuracy_rate"], 50.0)

    def test_detail_shows_backtest_and_pending(self):
        from django.core.management import call_command

        call_command("verify_formula_predictions")
        res = self.client.get(f"/lotto_formula/formula/{self.formula.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "ผลย้อนหลัง")
        self.assertContains(res, "รอตรวจ")
        stats = res.context["verified_stats"]
        self.assertEqual((stats["verified"], stats["correct"]), (2, 1))
        self.assertEqual(
            (stats["date_from"].isoformat(), stats["date_to"].isoformat()),
            ("2026-09-01", "2026-09-01"),
        )
