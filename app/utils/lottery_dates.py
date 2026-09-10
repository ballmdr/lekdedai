"""Contract งวดหวยรัฐบาลไทยสำหรับ MVP.

กติกา: ออกวันที่ 1 และ 16 ของทุกเดือน (1/16 มีทุกเดือนเสมอ).
โมดูลนี้สร้างขึ้นเพื่อแทน dependency ที่หายไป (`utils.lottery_dates`)
ที่ถูก import ใน 4 จุด: `home/views.py`, `lottery_checker/views.py`,
`lotto_stats/lotto_sync_service.py`, `sync_lotto_data.py`.

รูปแบบคืนค่า: string "YYYY-MM-DD" เสมอ เพื่อให้ตรงกับ code เดิมที่ใช้
`datetime.strptime(value, "%Y-%m-%d")`.
"""

from datetime import date, datetime


DRAW_DAYS = (1, 16)
DEFAULT_ALL_START = "2024-01-01"

_THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]


def _coerce_date(value):
    """รับ date/datetime/"YYYY-MM-DD" คืน date."""
    if value is None:
        return date.today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    raise TypeError(f"unsupported date type: {type(value)!r}")


def _next_month_first(d):
    if d.month == 12:
        return d.replace(year=d.year + 1, month=1, day=1)
    return d.replace(month=d.month + 1, day=1)


class LotteryDates:
    """API วันที่หวย — ใช้ได้ทั้ง `LotteryDates.xxx` และ `LOTTERY_DATES.xxx`."""

    @staticmethod
    def is_draw_date(value) -> bool:
        return _coerce_date(value).day in DRAW_DAYS

    @staticmethod
    def get_next_draw_date(from_date=None):
        """งวดถัดไปที่นับรวมวันนี้ (>= from_date) คืน "YYYY-MM-DD"."""
        d = _coerce_date(from_date)
        if d.day <= 1:
            candidate = d.replace(day=1)
        elif d.day <= 16:
            candidate = d.replace(day=16)
        else:
            candidate = _next_month_first(d)
        return candidate.isoformat()

    @staticmethod
    def get_recent_draw_dates(days_back, reference_date=None):
        """งวดใน [ref-days_back, ref] เรียงใหม่→เก่า (desc)."""
        ref = _coerce_date(reference_date)
        if days_back < 0:
            raise ValueError("days_back must be >= 0")
        start = ref.fromordinal(max(1, ref.toordinal() - days_back))
        out = []
        cur = ref
        while cur >= start:
            if cur.day in DRAW_DAYS:
                out.append(cur.isoformat())
            cur = cur.fromordinal(cur.toordinal() - 1)
        return out

    @staticmethod
    def get_all_draw_dates(start_date=None, end_date=None):
        """งวดทั้งหมดจาก start (default 2024-01-01) ถึง end (default งวดหน้า) เรียงเก่า→ใหม่."""
        start = _coerce_date(start_date or DEFAULT_ALL_START)
        end = _coerce_date(end_date) if end_date else _coerce_date(
            LotteryDates.get_next_draw_date(date.today())
        )
        if end < start:
            return []
        out = []
        # เดินทีละเดือน เก็บวันที่ 1 และ 16
        y, m = start.year, start.month
        while True:
            for day in DRAW_DAYS:
                try:
                    d = date(y, m, day)
                except ValueError:
                    continue
                if start <= d <= end:
                    out.append(d.isoformat())
            if y == end.year and m == end.month:
                break
            m += 1
            if m > 12:
                m, y = 1, y + 1
        return out

    @staticmethod
    def get_dropdown_options(limit=50, reference_date=None):
        """ตัวเลือก dropdown ใหม่→เก่า: {value, label, is_special}."""
        ref = _coerce_date(reference_date)
        if limit <= 0:
            return []
        out = []
        # เดินย้อนทีละเดือนจนครบ limit (กัน loop อนันต์ด้วย cap 1200 เดือน)
        y, m = ref.year, ref.month
        for _ in range(1200):
            for day in (16, 1):  # ใหม่ก่อนในเดือนเดียวกัน
                try:
                    d = date(y, m, day)
                except ValueError:
                    continue
                if d > ref:
                    continue
                out.append({
                    "value": d.isoformat(),
                    "label": f"{d.day} {_THAI_MONTHS[d.month - 1]} {d.year + 543}",
                    "is_special": False,
                })
                if len(out) >= limit:
                    return out
            m -= 1
            if m < 1:
                m, y = 12, y - 1
        return out


LOTTERY_DATES = LotteryDates()
