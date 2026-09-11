"""Task 4 regression tests: mutation endpoints ต้องกันคนทั่วไปออก."""
import json

from django.contrib.auth import get_user_model
from django.test import TestCase


class LotteryCheckerSecurityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user("staff", password="pw", is_staff=True)
        self.user = User.objects.create_user("plain", password="pw")

    def test_clear_anonymous_post_forbidden(self):
        res = self.client.post("/lottery_checker/api/lotto/clear/")
        self.assertEqual(res.status_code, 403)

    def test_clear_get_not_allowed(self):
        self.client.force_login(self.staff)
        res = self.client.get("/lottery_checker/api/lotto/clear/")
        self.assertEqual(res.status_code, 405)

    def test_clear_non_staff_forbidden(self):
        self.client.force_login(self.user)
        res = self.client.post("/lottery_checker/api/lotto/clear/")
        self.assertEqual(res.status_code, 403)

    def test_clear_staff_post_ok(self):
        self.client.force_login(self.staff)
        res = self.client.post("/lottery_checker/api/lotto/clear/")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

    def test_refresh_anonymous_post_forbidden(self):
        res = self.client.post(
            "/lottery_checker/api/lotto/refresh/",
            data=json.dumps({"date": "01", "month": "09", "year": "2026"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)

    def test_refresh_non_staff_forbidden(self):
        self.client.force_login(self.user)
        res = self.client.post(
            "/lottery_checker/api/lotto/refresh/",
            data=json.dumps({"date": "01", "month": "09", "year": "2026"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)

    def test_bulk_fetch_anonymous_post_forbidden(self):
        res = self.client.post(
            "/lottery_checker/api/lotto/bulk-fetch/",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)

    def test_bulk_fetch_get_not_allowed(self):
        self.client.force_login(self.staff)
        res = self.client.get("/lottery_checker/api/lotto/bulk-fetch/")
        self.assertEqual(res.status_code, 405)

    def test_public_read_endpoints_still_open(self):
        res = self.client.get("/lottery_checker/api/lotto/latest/?days=1")
        self.assertEqual(res.status_code, 200)


class HomepageHonestyTests(TestCase):
    """Task 5: DB ว่างต้องโชว์ empty state ห้ามโชว์เลข/เปอร์เซ็นต์จำลอง."""

    def test_empty_homepage_has_no_fake_accuracy(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, "87% แม่นยำ")
        self.assertContains(res, "ยังไม่มี")

    def test_homepage_single_main_path_ctas(self):
        """Task 8: CTA หลักพาไปวิเคราะห์ฝัน + ตรวจผล, ไม่มีลิงก์ตายใน nav."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'href="/dreams/"')
        self.assertContains(res, 'href="/lottery_checker/"')
        self.assertNotContains(res, 'href="#"')
        self.assertNotContains(res, "20/08/2025")

    def test_prediction_numbers_use_ranking_scores(self):
        from home.views import get_next_draw_prediction

        result = get_next_draw_prediction()
        for item in result["prediction_numbers"]:
            self.assertIn("score", item)
            self.assertNotIn("confidence", item)


class MockIngestionGatedTests(TestCase):
    """Task 5: mock ingestion ต้องปิดเป็น default."""

    def test_social_ingestion_off_by_default(self):
        from ai_engine.data_ingestion import DataIngestionManager
        from ai_engine.models import DataIngestionRecord, DataSource

        source = DataSource.objects.create(name="t", source_type="social_media")
        records = DataIngestionManager().collect_from_source(source)
        self.assertEqual(records, [])
        self.assertEqual(DataIngestionRecord.objects.count(), 0)

    def test_trends_ingestion_off_by_default(self):
        from ai_engine.data_ingestion import DataIngestionManager
        from ai_engine.models import DataIngestionRecord, DataSource

        source = DataSource.objects.create(name="t", source_type="trends")
        records = DataIngestionManager().collect_from_source(source)
        self.assertEqual(records, [])
        self.assertEqual(DataIngestionRecord.objects.count(), 0)


def _valid_payload(first="123456"):
    numbers = [{"value": first}]
    data = {
        "first": {"number": numbers},
        "second": {"number": [{"value": "111111"}]},
        "third": {"number": [{"value": "222222"}]},
        "fourth": {"number": [{"value": "333333"}]},
        "fifth": {"number": [{"value": "444444"}]},
    }
    return {"response": {"result": {"data": data}}}


class CanonicalSyncTests(TestCase):
    """Task 6: LottoResult canonical — sync ซ้ำไม่ซ้ำแถว ไม่ทับของดีด้วยของเสีย."""

    def test_repeat_save_no_duplicates(self):
        from datetime import date

        from lottery_checker.lotto_service import LottoService
        from lottery_checker.models import LottoResult

        svc = LottoService()
        day = date(2026, 9, 16)
        self.assertTrue(svc.save_to_database(_valid_payload(), day))
        self.assertTrue(svc.save_to_database(_valid_payload(), day))
        self.assertEqual(LottoResult.objects.filter(draw_date=day).count(), 1)

    def test_valid_not_overwritten_by_invalid(self):
        from datetime import date

        from lottery_checker.lotto_service import LottoService
        from lottery_checker.models import LottoResult

        svc = LottoService()
        day = date(2026, 9, 16)
        self.assertTrue(svc.save_to_database(_valid_payload("123456"), day))
        self.assertFalse(svc.save_to_database({"response": None}, day))
        row = LottoResult.objects.get(draw_date=day)
        self.assertTrue(row.is_valid)
        self.assertEqual(
            row.result_data["response"]["result"]["data"]["first"]["number"][0]["value"],
            "123456",
        )

    def test_invalid_then_valid_updates(self):
        from datetime import date

        from lottery_checker.lotto_service import LottoService
        from lottery_checker.models import LottoResult

        svc = LottoService()
        day = date(2026, 9, 16)
        self.assertTrue(svc.save_to_database({"response": None}, day))
        self.assertFalse(LottoResult.objects.get(draw_date=day).is_valid)
        self.assertTrue(svc.save_to_database(_valid_payload(), day))
        row = LottoResult.objects.get(draw_date=day)
        self.assertTrue(row.is_valid)
        self.assertEqual(LottoResult.objects.filter(draw_date=day).count(), 1)


class QuickCheckConsistencyTests(TestCase):
    """หน้าแรก quick check ต้องได้ผลเดียวกับข้อมูล canonical (raw GLO payload)."""

    def setUp(self):
        from datetime import date

        from lottery_checker.lotto_service import LottoService

        data = {
            "first": {"number": [{"value": "417212"}]},
            "second": {"number": [{"value": "111111"}]},
            "third": {"number": [{"value": "222222"}]},
            "fourth": {"number": [{"value": "333333"}]},
            "fifth": {"number": [{"value": "444444"}]},
            "last3f": {"number": [{"value": "417"}]},
            "last3b": {"number": [{"value": "212"}]},
            "last2": {"number": [{"value": "12"}]},
            "near1": {"number": [{"value": "417211"}]},
        }
        payload = {"response": {"result": {"data": data}}}
        LottoService().save_to_database(payload, date(2026, 9, 1))

    def _check(self, number):
        return self.client.post(
            "/lottery_checker/api/check/",
            data=json.dumps({"lottery_number": number}),
            content_type="application/json",
        ).json()

    def test_first_prize_is_winner(self):
        body = self._check("417212")
        self.assertTrue(body["success"])
        self.assertTrue(body["result"]["is_winner"])
        self.assertIn("รางวัลที่ 1", body["result"]["message"])

    def test_last2_prize_derived_from_six_digits(self):
        body = self._check("999912")
        self.assertTrue(body["result"]["is_winner"])
        self.assertIn("เลขท้าย 2 ตัว", body["result"]["message"])

    def test_non_winner(self):
        body = self._check("000000")
        self.assertFalse(body["result"]["is_winner"])
        self.assertIn("ไม่ถูกรางวัล", body["result"]["message"])


def _leading_zero_payload():
    """fixture ครอบคลุมเลขศูนย์นำหน้า (first 012345, last2 มี 00)."""
    def nums(*values):
        return {"number": [{"value": v} for v in values]}

    data = {
        "first": nums("012345"),
        "second": nums("111111"),
        "third": nums("222222"),
        "fourth": nums("333333"),
        "fifth": nums("444444"),
        "last3f": nums("012", "990"),
        "last3b": nums("345", "007"),
        "last2": nums("45", "00"),
        "near1": nums("012344"),
    }
    return {"response": {"result": {"data": data}}}


class CheckRulesLeadingZeroTests(TestCase):
    """Task 11: กติกาตรวจต้องถูกกับเลขศูนย์นำหน้า และเลข 2/3/6 หลัก."""

    def test_six_digit_first_with_derived(self):
        from lottery_checker.lotto_service import check_numbers_against_result

        self.assertEqual(
            check_numbers_against_result(_leading_zero_payload(), "012345"),
            [
                "รางวัลที่ 1 (6,000,000 บาท)",
                "เลขหน้า 3 ตัว (4,000 บาท)",
                "เลขท้าย 3 ตัว (4,000 บาท)",
                "เลขท้าย 2 ตัว (2,000 บาท)",
            ],
        )

    def test_front_three_only(self):
        from lottery_checker.lotto_service import check_numbers_against_result

        self.assertEqual(
            check_numbers_against_result(_leading_zero_payload(), "990012"),
            ["เลขหน้า 3 ตัว (4,000 บาท)"],
        )

    def test_back_three_only(self):
        from lottery_checker.lotto_service import check_numbers_against_result

        self.assertEqual(
            check_numbers_against_result(_leading_zero_payload(), "123007"),
            ["เลขท้าย 3 ตัว (4,000 บาท)"],
        )

    def test_three_digit_matches_back(self):
        from lottery_checker.lotto_service import check_numbers_against_result

        self.assertEqual(
            check_numbers_against_result(_leading_zero_payload(), "345"),
            ["เลขท้าย 3 ตัว (4,000 บาท)"],
        )

    def test_two_digit_with_leading_zero(self):
        from lottery_checker.lotto_service import check_numbers_against_result

        self.assertEqual(
            check_numbers_against_result(_leading_zero_payload(), "00"),
            ["เลขท้าย 2 ตัว (2,000 บาท)"],
        )
        self.assertEqual(
            check_numbers_against_result(_leading_zero_payload(), "09"), []
        )

    def test_non_winner(self):
        from lottery_checker.lotto_service import check_numbers_against_result

        self.assertEqual(
            check_numbers_against_result(_leading_zero_payload(), "000001"), []
        )

    def test_malformed_returns_none(self):
        from lottery_checker.lotto_service import check_numbers_against_result

        self.assertIsNone(check_numbers_against_result("not-a-dict", "012345"))


class CheckDrawApiTests(TestCase):
    """Task 11: API ตรวจต่องวดแบบ read-only — won/lost/pending/stale/error."""

    def setUp(self):
        from datetime import timedelta

        from django.utils import timezone

        from lottery_checker.lotto_service import LottoService
        from lottery_checker.models import LottoResult

        self.today = timezone.localdate()
        svc = LottoService()
        self.won_day = self.today - timedelta(days=10)
        self.assertTrue(svc.save_to_database(_leading_zero_payload(), self.won_day))
        self.invalid_day = self.today - timedelta(days=11)
        self.assertTrue(svc.save_to_database({"response": None}, self.invalid_day))
        self.assertFalse(
            LottoResult.objects.get(draw_date=self.invalid_day).is_valid
        )
        self.missing_recent_day = self.today - timedelta(days=1)
        self.stale_day = self.today - timedelta(days=20)
        self.future_day = self.today + timedelta(days=30)

    def _check(self, draw_date, number):
        return self.client.post(
            "/lottery_checker/api/check-draw/",
            data=json.dumps({"draw_date": draw_date, "number": number}),
            content_type="application/json",
        )

    def test_won(self):
        res = self._check(self.won_day.isoformat(), "012345")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["status"], "won")
        self.assertTrue(body["is_winner"])
        self.assertIn("รางวัลที่ 1", body["message"])

    def test_lost_states_scope(self):
        res = self._check(self.won_day.isoformat(), "000001")
        body = res.json()
        self.assertEqual(body["status"], "lost")
        self.assertFalse(body["is_winner"])
        self.assertIn("กติกา", body["message"])

    def test_two_digit_won(self):
        body = self._check(self.won_day.isoformat(), "00").json()
        self.assertEqual(body["status"], "won")
        self.assertIn("เลขท้าย 2 ตัว", body["message"])

    def test_unsupported_length_rejected(self):
        res = self._check(self.won_day.isoformat(), "1234")
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()["success"])

    def test_bad_date_rejected(self):
        res = self._check("2026-13-99", "012345")
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()["success"])

    def test_pending_future(self):
        body = self._check(self.future_day.isoformat(), "012345").json()
        self.assertEqual(body["status"], "pending")
        self.assertFalse(body["is_winner"])

    def test_pending_recent_missing(self):
        body = self._check(self.missing_recent_day.isoformat(), "012345").json()
        self.assertEqual(body["status"], "pending")

    def test_stale_when_missing_beyond_grace(self):
        body = self._check(self.stale_day.isoformat(), "012345").json()
        self.assertEqual(body["status"], "stale")

    def test_error_when_stored_result_invalid(self):
        body = self._check(self.invalid_day.isoformat(), "012345").json()
        self.assertEqual(body["status"], "error")

    def test_does_not_fetch_or_create_rows(self):
        from lottery_checker.models import LottoResult

        self.assertFalse(LottoResult.objects.filter(draw_date=self.stale_day).exists())
        self._check(self.stale_day.isoformat(), "012345")
        self.assertFalse(LottoResult.objects.filter(draw_date=self.stale_day).exists())


class SecurityAbuseTests(TestCase):
    """Task 23: rate limit, payload cap, ไม่รั่ว error ภายใน."""

    def _post_draw(self, draw_date, number):
        return self.client.post(
            "/lottery_checker/api/check-draw/",
            data=json.dumps({"draw_date": draw_date, "number": number}),
            content_type="application/json",
        )

    def test_rate_limit_returns_429(self):
        from django.core.cache import cache
        from django.test import override_settings

        cache.clear()
        with override_settings(
            RATELIMIT_OVERRIDES={"lottery_checker.views.check_draw": "2/m"}
        ):
            self.assertEqual(
                self._post_draw("2026-09-01", "012345").status_code, 200
            )
            self.assertEqual(
                self._post_draw("2026-09-01", "012345").status_code, 200
            )
            res = self._post_draw("2026-09-01", "012345")
            self.assertEqual(res.status_code, 429)
            self.assertFalse(res.json()["success"])

    def test_oversized_body_rejected(self):
        res = self.client.post(
            "/lottery_checker/api/lotto/check/",
            data=json.dumps({
                "date": "01", "month": "09", "year": "2026",
                "number": "0" * 5000,
            }),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 413)

    def test_server_error_hides_internals_in_prod(self):
        from datetime import date
        from unittest.mock import patch

        from django.test import override_settings

        from lottery_checker.lotto_service import LottoService

        self.assertTrue(
            LottoService().save_to_database(_leading_zero_payload(), date(2026, 9, 1))
        )
        with patch(
            "lottery_checker.views.check_numbers_against_result",
            side_effect=RuntimeError("db exploded: SECRET=xyz"),
        ), override_settings(DEBUG=False):
            res = self._post_draw("2026-09-01", "012345")
        self.assertEqual(res.status_code, 500)
        body = res.json()
        self.assertEqual(body["error"], "เกิดข้อผิดพลาดในระบบ กรุณาลองใหม่")
        self.assertNotIn("SECRET", res.content.decode())
