"""Task 28/30: สรุป funnel/activation/retention รายงวด จาก AnalyticsEvent.

อ่านเฉพาะ event ที่ไม่เก็บข้อความฝัน/เลข/IP — ใช้ตัดสินใจช่วง beta.
"""
from datetime import timedelta

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


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator * 100, 1)


def build_report(days=30, draws=None):
    """คืน dict สรุปทั้งหมด (ไม่ throw) — draws = จำกัดเฉพาะ N งวดล่าสุด."""
    since = timezone.now() - timedelta(days=days)
    events = AnalyticsEvent.objects.filter(created_at__gte=since)

    total = events.count()
    sessions = events.values("session_id").distinct().count()

    funnel = []
    for name, label in FUNNEL:
        count = events.filter(name=name).values("session_id").distinct().count()
        funnel.append({
            "name": name,
            "label": label,
            "sessions": count,
            "pct": _rate(count, sessions),
        })

    per_draw = (
        events.exclude(draw_period=None)
        .values("draw_period", "name")
        .annotate(sessions=Count("session_id", distinct=True))
    )
    draw_rows = {}
    for row in per_draw:
        draw_rows.setdefault(row["draw_period"], {})[row["name"]] = row["sessions"]

    session_per_draw = dict(
        events.exclude(draw_period=None)
        .values_list("draw_period")
        .annotate(sessions=Count("session_id", distinct=True))
    )

    ordered = sorted(draw_rows)
    if draws:
        ordered = ordered[-draws:]

    draw_summaries = []
    for draw in ordered:
        rows = draw_rows[draw]
        started = rows.get("dream_started", 0)
        completed = rows.get("dream_completed", 0)
        saved = rows.get("number_saved", 0)
        checked = rows.get("result_checked", 0)
        draw_summaries.append({
            "draw_period": draw.isoformat(),
            "sessions": session_per_draw.get(draw, 0),
            "activation": saved,
            "dream_started": started,
            "dream_completed": completed,
            "number_saved": saved,
            "result_checked": checked,
            "history_viewed": rows.get("history_viewed", 0),
            "completion_rate": _rate(completed, started),
            "save_rate": _rate(saved, completed),
            "result_check_rate": _rate(checked, saved),
        })

    multi = (
        events.exclude(draw_period=None)
        .values("session_id")
        .annotate(draws=Count("draw_period", distinct=True))
        .filter(draws__gte=2)
        .count()
    )

    return {
        "generated_at": timezone.now().isoformat(),
        "window_days": days,
        "totals": {"events": total, "sessions": sessions},
        "funnel": funnel,
        "draws": draw_summaries,
        "retention": {
            "multi_draw_sessions": multi,
            "sessions": sessions,
            "pct": _rate(multi, sessions),
        },
    }


def format_text(report, title="รายงาน analytics"):
    lines = [
        title,
        f"สร้างเมื่อ {report['generated_at']}",
        f"ช่วง {report['window_days']} วัน: "
        f"{report['totals']['events']} events, {report['totals']['sessions']} เซสชัน",
        "",
        "== Funnel (unique session) ==",
    ]
    for item in report["funnel"]:
        pct = f"{item['pct']:.1f}%" if item["pct"] is not None else "-"
        lines.append(f"  {item['label']:20s} {item['sessions']:5d}  ({pct})")

    lines.append("")
    lines.append("== รายงวด (activation / completion / result-check) ==")
    if not report["draws"]:
        lines.append("  ยังไม่มี event ที่ผูกกับงวด")
    for draw in report["draws"]:
        completion = (
            f"{draw['completion_rate']}%" if draw["completion_rate"] is not None else "-"
        )
        result = (
            f"{draw['result_check_rate']}%" if draw["result_check_rate"] is not None else "-"
        )
        lines.append(
            f"  งวด {draw['draw_period']}: sessions {draw['sessions']}, "
            f"activation {draw['activation']}, completion {completion}, "
            f"result-check {result} "
            f"(บันทึก {draw['number_saved']}, ตรวจ {draw['result_checked']})"
        )

    retention = report["retention"]
    ret_pct = f"{retention['pct']:.1f}%" if retention["pct"] is not None else "-"
    lines.append("")
    lines.append("== Cross-draw retention ==")
    lines.append(
        f"  กลับมา ≥2 งวด: {retention['multi_draw_sessions']} เซสชัน "
        f"({ret_pct} ของเซสชันทั้งหมด)"
    )
    return "\n".join(lines)
