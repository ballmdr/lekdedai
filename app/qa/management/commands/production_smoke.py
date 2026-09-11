"""Task 31: production smoke test — health, route หลัก, static และผลหวยล่าสุด.

ตัวอย่าง:
    python app/manage.py production_smoke --base-url https://lekdedai.com
ใช้ใน deploy step/หลัง deploy โดย exit 1 เมื่อพบปัญหา (ผูกกับ monitor ได้).
"""
import os

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

SMOKE_ROUTES = [
    "/",
    "/dreams/",
    "/lottery_checker/",
    "/notebook/",
    "/lotto_stats/",
    "/news/",
    "/lotto_formula/",
    "/ai/",
    "/static/css/tailwind.css",
]


def collect_http_issues(base_url, routes=None, timeout=10):
    """ตรวจ HTTP จริง คืน list ปัญหา (ไม่ throw)."""
    routes = routes if routes is not None else SMOKE_ROUTES
    issues = []
    base = base_url.rstrip("/")

    try:
        health = requests.get(f"{base}/health/", timeout=timeout)
        if health.status_code != 200:
            body = {}
            try:
                body = health.json()
            except ValueError:
                body = {}
            issues.append(
                f"/health/ -> {health.status_code} "
                f"{body.get('problems', body.get('status', ''))}"
            )
    except requests.RequestException as exc:
        issues.append(f"/health/ เข้าไม่ถึง: {type(exc).__name__}")

    for route in routes:
        if route == "/health/":
            continue
        try:
            res = requests.get(f"{base}{route}", timeout=timeout)
            if res.status_code == 200:
                continue
            # ช่วง closed beta: 302 ไป /beta/ ถือว่าแอปยังทำงานปกติ
            location = res.headers.get("Location", "")
            if res.status_code in (301, 302, 303, 307, 308) and "/beta/" in location:
                continue
            issues.append(f"GET {route} -> {res.status_code}")
        except requests.RequestException as exc:
            issues.append(f"GET {route} เข้าไม่ถึง: {type(exc).__name__}")

    return issues


def collect_db_issues(max_stale_days=40, now=None):
    """ตรวจว่ามีผลหวยล่าสุดและไม่เก่าเกินกำหนด (รันบนเครื่องที่ต่อ DB).

    เช็คสองชั้น: (1) ผลงวดล่าสุดตามตาราง 1/16 ต้องมี เว้นแต่วันนี้เพิ่งเป็นวันออกผล
    (2) กันเหนียวถ้าข้อมูลเก่ากว่า max_stale_days (ค่าเริ่มต้น 40 วัน)
    """
    from lottery_checker.models import LottoResult
    from utils.lottery_dates import LotteryDates

    now = now or timezone.now()
    issues = []
    latest = LottoResult.objects.filter(is_valid=True).order_by("-draw_date").first()
    if latest is None:
        issues.append("ไม่มีผลหวยในฐานข้อมูล (LottoResult ว่าง)")
        return issues

    expected = LotteryDates.get_recent_draw_dates(400, reference_date=now.date())
    expected_latest = expected[0] if expected else None
    if (
        expected_latest
        and expected_latest != now.date().isoformat()
        and latest.draw_date.isoformat() < expected_latest
    ):
        issues.append(
            f"ยังไม่มีผลงวดล่าสุด {expected_latest} (ล่าสุดในระบบ {latest.draw_date})"
        )

    age_days = (now.date() - latest.draw_date).days
    if age_days > max_stale_days:
        issues.append(
            f"ผลหวยล่าสุดเก่า {age_days} วัน (งวด {latest.draw_date}, "
            f"เกิน {max_stale_days} วัน)"
        )
    return issues


class Command(BaseCommand):
    help = "Smoke test production: /health/, route หลัก, static, ผลหวยล่าสุด"

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url", type=str,
            default=os.environ.get("SMOKE_BASE_URL", ""),
            help="เช่น https://lekdedai.com (ว่าง = ข้าม HTTP ตรวจเฉพาะ DB)",
        )
        parser.add_argument("--timeout", type=int, default=10)
        parser.add_argument(
            "--max-stale-days", type=int, default=40,
            help="กันเหนียวเมื่อข้อมูลเก่ากว่านี้ (ตารางงวด 1/16 ถูกเช็คแยกอยู่แล้ว)",
        )

    def handle(self, *args, **options):
        issues = []

        base_url = options["base_url"]
        if base_url:
            self.stdout.write(f"ตรวจ HTTP: {base_url}")
            issues += collect_http_issues(base_url, timeout=options["timeout"])
        else:
            self.stdout.write(
                "ไม่ได้ระบุ --base-url/SMOKE_BASE_URL — ตรวจเฉพาะฐานข้อมูล"
            )

        issues += collect_db_issues(max_stale_days=options["max_stale_days"])

        if issues:
            for issue in issues:
                self.stdout.write(self.style.ERROR(f"FAIL: {issue}"))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("PRODUCTION SMOKE PASSED"))
