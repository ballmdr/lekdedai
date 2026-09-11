"""Task 15: กติกาตรวจผลย้อนหลังของสูตร (ประกาศชัด ทดสอบได้).

กติกาที่ประกาศ: การทำนาย 1 แถว (เลข 3 ตัว คั่นจุลภาค) ถือว่า "ถูก" ก็ต่อเมื่อ
มีเลขอย่างน้อย 1 ชุดตรงกับเลขรางวัลหน้า/ท้าย 3 ตัวของงวดนั้น โดยเทียบกับ
LotteryDraw ที่ sync จาก LottoResult (canonical) แล้วเท่านั้น.
นับผลเฉพาะแถวที่ตรวจแล้ว (is_correct ไม่ใช่ None) — แถวรอตรวจไม่นับทั้งเศษและส่วน.
"""
from django.utils import timezone

from lotto_stats.models import LotteryDraw

from .models import LotteryFormula, Prediction

VERIFICATION_RULE = (
    "ถูก = เลข 3 ตัวที่ทำนายตรงกับเลขรางวัลหน้า/ท้าย 3 ตัวของงวดนั้น"
    "อย่างน้อย 1 ชุด (เทียบกับผลหวยที่ยืนยันแล้ว)"
)


def parse_predicted_numbers(text):
    """แยกเลขทำนายเป็น list ของเลข 3 หลัก (ตัดค่าว่าง/ค่าผิดรูปทิ้ง)."""
    if not text:
        return []
    return [p.strip() for p in str(text).split(",") if p.strip().isdigit() and len(p.strip()) == 3]


def check_prediction_against_draw(predicted, draw):
    """ตรวจเลขทำนายกับผลงวดเดียว คืน dict {won, matched, actual}."""
    actual = draw.get_all_three_digits()
    matched = [num for num in predicted if num in actual]
    return {"won": len(matched) > 0, "matched": matched, "actual": actual}


def verify_pending_predictions():
    """ตรวจ Prediction ที่ค้าง (is_correct None และงวดผ่านมาแล้ว).

    งวดที่ยังไม่มี LotteryDraw จะคงสถานะรอตรวจไว้ (ไม่เดา).
    อัปเดตตัวนับผลวัดของสูตรจากแถวที่ตรวจแล้วเท่านั้น.
    คืน dict สรุป {checked, won, lost, skipped_no_result}.
    """
    today = timezone.localdate()
    pending = Prediction.objects.filter(
        is_correct__isnull=True, draw_date__lt=today
    ).select_related("formula")

    summary = {"checked": 0, "won": 0, "lost": 0, "skipped_no_result": 0}
    touched_formulas = set()

    for prediction in pending:
        draw = LotteryDraw.objects.filter(draw_date=prediction.draw_date).first()
        if draw is None:
            summary["skipped_no_result"] += 1
            continue

        predicted = parse_predicted_numbers(prediction.predicted_numbers)
        result = check_prediction_against_draw(predicted, draw)
        prediction.is_correct = result["won"]
        prediction.verified_at = timezone.now()
        prediction.save(update_fields=["is_correct", "verified_at"])
        summary["checked"] += 1
        summary["won" if result["won"] else "lost"] += 1
        touched_formulas.add(prediction.formula_id)

    for formula_id in touched_formulas:
        verified = Prediction.objects.filter(
            formula_id=formula_id, is_correct__isnull=False
        )
        correct = verified.filter(is_correct=True).count()
        total = verified.count()
        formula = LotteryFormula.objects.get(id=formula_id)
        formula.correct_predictions = correct
        formula.verified_count = total
        formula.accuracy_rate = (correct / total * 100) if total else 0
        formula.save(update_fields=[
            "correct_predictions", "verified_count", "accuracy_rate",
        ])

    return summary


def get_verified_stats(formula):
    """สถิติผลย้อนหลังของสูตร: {verified, correct, date_from, date_to, rule}."""
    verified = Prediction.objects.filter(
        formula=formula, is_correct__isnull=False
    ).order_by("draw_date")
    first = verified.first()
    last = verified.last()
    return {
        "verified": verified.count(),
        "correct": verified.filter(is_correct=True).count(),
        "date_from": first.draw_date if first else None,
        "date_to": last.draw_date if last else None,
        "rule": VERIFICATION_RULE,
    }
