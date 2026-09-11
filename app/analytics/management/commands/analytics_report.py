"""Task 28: รายงาน analytics รายงวด — activation, result-check, cross-draw retention."""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from analytics.models import AnalyticsEvent

FUNNEL = [
    ("landing_view", "เปิดหน้าแรก"),
    ("dream_started", "เริ่มวิเคราะห์ฝัน"),
    ("dream_completed", "วิเคราะห์ฝันสำเร็จ"),
    ("number_saved", "บันทึกเลข"),
    ("result_checked", "ตรวจผลหวย"),
    ("history_viewed", "ดูประวัติ"),
    ("formula_used", "ใช้สูตร"),
    ("news_opened", "เปิดข่าว"),
    ("share_used", "แชร์"),
]


class Command(BaseCommand):
    help = "รายงาน funnel/activation/retention จาก analytics (ไม่รวมข้อความฝัน/เลข/IP)"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)

    def handle(self, *args, **options):
        since = timezone.now() - timedelta(days=options["days"])
        events = AnalyticsEvent.objects.filter(created_at__gte=since)

        total = events.count()
        sessions = events.values("session_id").distinct().count()
        self.stdout.write(f"ช่วง {options['days']} วัน: {total} events, {sessions} เซสชัน")

        self.stdout.write("\n== Funnel (unique session) ==")
        for name, label in FUNNEL:
            count = events.filter(name=name).values("session_id").distinct().count()
            pct = (count / sessions * 100) if sessions else 0
            self.stdout.write(f"  {label:20s} {count:5d}  ({pct:.1f}%)")

        self.stdout.write("\n== รายงวด (activation / result-check) ==")
        per_draw = (
            events.exclude(draw_period=None)
            .values("draw_period", "name")
            .annotate(sessions=Count("session_id", distinct=True))
        )
        draws = sorted({row["draw_period"] for row in per_draw})
        for draw in draws:
            rows = {r["name"]: r["sessions"] for r in per_draw if r["draw_period"] == draw}
            self.stdout.write(
                f"  งวด {draw:%d/%m/%Y}: "
                f"activation {rows.get('dream_completed', 0)}, "
                f"number_saved {rows.get('number_saved', 0)}, "
                f"result_checked {rows.get('result_checked', 0)}"
            )

        self.stdout.write("\n== Cross-draw retention ==")
        multi = (
            events.exclude(draw_period=None)
            .values("session_id")
            .annotate(draws=Count("draw_period", distinct=True))
            .filter(draws__gte=2)
            .count()
        )
        pct = (multi / sessions * 100) if sessions else 0
        self.stdout.write(
            f"  กลับมา ≥2 งวด: {multi} เซสชัน ({pct:.1f}% ของเซสชันทั้งหมด)"
        )
