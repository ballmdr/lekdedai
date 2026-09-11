"""Task 13: focused unit tests — นิยามสถิติต้องแยกเลขท้าย 2 ตัวออกจากเลขในรางวัลที่ 1."""
from datetime import date, timedelta

from django.test import TestCase

from lotto_stats.models import LotteryDraw
from lotto_stats.stats_calculator import StatsCalculator


def _make_draws():
    """fixture 5 งวด รวมเลขซ้ำและเลขศูนย์นำหน้า (คำนวณด้วยมือได้)."""
    rows = [
        # (draw_date, first_prize, two_digit, front, back)
        (date(2026, 9, 1), "417212", "04", "111,222", "333,444"),
        (date(2026, 8, 16), "004615", "53", "007,123", "007,999"),
        (date(2026, 8, 1), "932479", "04", "012,345", "678,004"),
        (date(2026, 7, 16), "100009", "00", "100,200", "300,009"),
        (date(2026, 7, 1), "123045", "45", "123,456", "789,045"),
    ]
    for draw_date, first, two, front, back in rows:
        LotteryDraw.objects.create(
            draw_date=draw_date,
            first_prize=first,
            two_digit=two,
            three_digit_front=front,
            three_digit_back=back,
        )


class HotColdPositionTests(TestCase):
    """เลขท้าย 2 ตัวต้องไม่ปนกับเลข 2 หลักในรางวัลที่ 1."""

    def setUp(self):
        _make_draws()
        self.calc = StatsCalculator()

    def test_hot_two_digit_counts_only_two_digit_prize(self):
        hot = self.calc.get_hot_numbers(limit=10, days=4000, number_type="2D")
        top = hot[0]
        # two_digit: 04 x2, 53/00/45 x1 — '00' ในรางวัลที่ 1 ต้องไม่ถูกนับรวม
        self.assertEqual(top["number"], "04")
        self.assertEqual(top["count"], 2)
        self.assertEqual(top["percentage"], 40.0)

    def test_hot_percentage_never_exceeds_100(self):
        hot = self.calc.get_hot_numbers(limit=100, days=4000, number_type="2D")
        for item in hot:
            self.assertLessEqual(item["percentage"], 100)

    def test_hot_first_prize_pairs_counts_windows(self):
        pairs = self.calc.get_hot_first_prize_pairs(limit=10, days=4000)
        top = pairs[0]
        # '00': B x1 + D x3 = 4 ครั้ง ใน 2 งวด
        self.assertEqual(top["number"], "00")
        self.assertEqual(top["count"], 4)
        self.assertEqual(top["draws"], 2)
        self.assertEqual(top["percentage"], 40.0)

    def test_cold_two_digit_uses_latest_two_digit_only(self):
        cold = {c["number"]: c for c in self.calc.get_cold_numbers(limit=100)}
        # '04' ออกท้าย 2 ตัวล่าสุด 01/09/2026 (แม้จะอยู่ในรางวัลที่ 1 งวดอื่นด้วย)
        self.assertEqual(cold["04"]["days"], (date.today() - date(2026, 9, 1)).days)
        # '45' ออกท้าย 2 ตัวครั้งเดียว 01/07/2026
        self.assertEqual(cold["45"]["days"], (date.today() - date(2026, 7, 1)).days)
        days = [c["days"] for c in self.calc.get_cold_numbers(limit=100)]
        self.assertEqual(days, sorted(days, reverse=True))

    def test_cold_pairs_uses_first_prize_windows(self):
        cold = {c["number"]: c for c in self.calc.get_cold_first_prize_pairs(limit=100)}
        # '04' อยู่ในรางวัลที่ 1 ล่าสุดงวด 16/08/2026 (B) ไม่ใช่งวดท้าย 2 ตัวล่าสุด
        self.assertEqual(cold["04"]["days"], (date.today() - date(2026, 8, 16)).days)
        # '23' ปรากฏแค่หน้าต่างรางวัลที่ 1 งวด 01/07/2026 (E)
        self.assertEqual(cold["23"]["days"], (date.today() - date(2026, 7, 1)).days)


class NumberStatisticsSplitTests(TestCase):
    def setUp(self):
        _make_draws()
        self.calc = StatsCalculator()

    def test_two_digit_stats_come_from_two_digit_only(self):
        stats = self.calc.get_number_statistics("04")
        # ท้าย 2 ตัว: 01/09 + 01/08 = 2 ครั้ง ห่างกัน 31 วัน
        self.assertEqual(stats["total_appearances"], 2)
        self.assertEqual(stats["appearance_dates"], ["01/09/2026", "01/08/2026"])
        self.assertEqual(stats["average_gap"], 31.0)
        self.assertEqual(stats["max_gap"], 31)
        self.assertEqual(stats["min_gap"], 31)
        # ในรางวัลที่ 1: B (16/08) + E (01/07) = 2 งวด
        self.assertEqual(stats["first_prize"]["total_appearances"], 2)
        self.assertEqual(stats["first_prize"]["appearance_dates"][0], "16/08/2026")

    def test_leading_zero_two_digit(self):
        stats = self.calc.get_number_statistics("00")
        self.assertEqual(stats["total_appearances"], 1)
        self.assertEqual(stats["appearance_dates"], ["16/07/2026"])
        self.assertEqual(stats["first_prize"]["total_appearances"], 2)

    def test_positions_label_present(self):
        stats = self.calc.get_number_statistics("04")
        self.assertIn("เลขท้าย 2 ตัว", stats["positions"])
        stats3 = self.calc.get_number_statistics("007")
        self.assertIn("3 ตัว", stats3["positions"])


class MonthlyAndSummarySplitTests(TestCase):
    def setUp(self):
        _make_draws()
        self.calc = StatsCalculator()

    def test_monthly_splits_positions(self):
        monthly = self.calc.get_monthly_statistics()
        sept = monthly["กันยายน"]
        self.assertEqual(sept["total_draws"], 1)
        self.assertEqual(sept["most_common_two_digit"], {"number": "04", "count": 1})
        # รางวัลที่ 1 งวด A: 41/17/72/21/12 อย่างละครั้ง
        self.assertEqual(sept["most_common_first_pair"]["count"], 1)
        aug = monthly["สิงหาคม"]
        self.assertEqual(aug["total_draws"], 2)

    def test_summary_splits_positions(self):
        summary = self.calc.get_statistics_summary()
        self.assertEqual(summary["total_draws"], 5)
        self.assertEqual(
            summary["most_common_all_time"]["two_digit"], {"number": "04", "count": 2}
        )
        self.assertEqual(
            summary["most_common_all_time"]["first_prize_pair"],
            {"number": "00", "count": 4},
        )


class DoubleSequentialSplitTests(TestCase):
    def setUp(self):
        _make_draws()
        self.calc = StatsCalculator()

    def test_double_counts_split_by_position(self):
        doubles = self.calc.get_double_number_stats(days_back=4000)["2d"]
        # '00': ท้าย 2 ตัวงวด D x1; หน้าต่างรางวัลที่ 1: B x1 + D x3
        self.assertEqual(doubles["00"]["count_two_digit"], 1)
        self.assertEqual(doubles["00"]["count_first_prize"], 4)
        self.assertEqual(doubles["00"]["count"], 5)
        self.assertEqual(doubles["99"]["count"], 0)

    def test_sequential_counts_split_by_position(self):
        seq = self.calc.get_sequential_number_stats(days_back=4000)["2d"]
        # '45' (เรียงขึ้น): ท้าย 2 ตัวงวด E x1; หน้าต่างรางวัลที่ 1 งวด E x1
        self.assertEqual(seq["45"]["count_two_digit"], 1)
        self.assertEqual(seq["45"]["count_first_prize"], 1)
        self.assertEqual(seq["45"]["count"], 2)
        # '12' (เรียงขึ้น): ไม่เคยเป็นท้าย 2 ตัว; หน้าต่าง A+E x2
        self.assertEqual(seq["12"]["count_two_digit"], 0)
        self.assertEqual(seq["12"]["count_first_prize"], 2)


class NumberDetailApiTests(TestCase):
    def setUp(self):
        _make_draws()

    def test_detail_splits_positions(self):
        res = self.client.get("/lotto_stats/api/number/04/")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["statistics"]["total_appearances"], 2)
        self.assertEqual(body["statistics"]["first_prize"]["total_appearances"], 2)
        types = [r["type"] for r in body["recent_appearances"]]
        self.assertIn("เลขท้าย 2 ตัว", types)
        self.assertTrue(any("รางวัลที่ 1 (ตำแหน่ง" in t for t in types))

    def test_statistics_page_renders_split_metrics(self):
        res = self.client.get("/lotto_stats/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "เลขคู่พบบ่อยในรางวัลที่ 1")
        self.assertContains(res, "งวดละ 1 ค่า")
