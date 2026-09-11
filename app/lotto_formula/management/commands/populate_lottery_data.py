from django.core.management.base import BaseCommand

from lotto_formula.models import LotteryFormula

REFERENCE_INPUT_SPEC = {
    "reference_digits": {
        "type": "string",
        "pattern": "^[0-9]{2,}$",
        "description": "เลขอ้างอิงอย่างน้อย 2 หลัก (ใช้เฉพาะตัวเลข)",
    }
}
THREE_NUMBERS_OUTPUT_SPEC = {
    "type": "array",
    "count": 3,
    "items": {"type": "string", "pattern": "^[0-9]{3}$"},
    "description": "เลข 3 หลัก 3 ชุด (deterministic ต่อ input เดิม)",
}

# Task 14: ทะเบียนสูตรที่อนุมัติ — deterministic, ไม่มีผลหวย/ผลวัดปลอม.
# code คือตัวตนของสูตร (views dispatch ด้วย code) version ไว้ตามรอยเปลี่ยนสูตร.
FORMULA_REGISTRY = [
    {
        "code": "sum_diff",
        "version": "1.0",
        "name": "สูตรบวกลบ",
        "description": "สูตรคำนวณโดยการบวกลบเลขอ้างอิง เหมาะสำหรับผู้เริ่มต้น",
        "method": (
            "วิธีการคำนวณ:\n"
            "1. เอาเลข 2 ตัวแรกจากเลขอ้างอิงมาบวกกัน\n"
            "2. เอาเลข 2 ตัวแรกมาลบกัน\n"
            "3. เอาเลข 2 ตัวแรกมาคูณกัน\n"
            "4. นำผลลัพธ์มาจัดเรียงเป็นเลข 3 ตัว"
        ),
        "input_spec": REFERENCE_INPUT_SPEC,
        "output_spec": THREE_NUMBERS_OUTPUT_SPEC,
    },
    {
        "code": "running",
        "version": "1.0",
        "name": "สูตรเลขวิ่ง",
        "description": "สูตรคำนวณเลขที่วิ่งตามลำดับ เหมาะสำหรับเลขท้าย 3 ตัว",
        "method": (
            "วิธีการคำนวณ:\n"
            "1. เอาเลขตัวแรกจากเลขอ้างอิงเป็นเลขฐาน\n"
            "2. บวกเพิ่มทีละ 1 ไปเรื่อยๆ\n"
            "3. ถ้าเกิน 9 ให้เริ่มใหม่ที่ 0"
        ),
        "input_spec": REFERENCE_INPUT_SPEC,
        "output_spec": THREE_NUMBERS_OUTPUT_SPEC,
    },
    {
        "code": "reverse",
        "version": "1.0",
        "name": "สูตรเลขกลับ",
        "description": "สูตรคำนวณโดยการกลับเลขและคำนวณ ผลลัพธ์เป็นเลข 3 หลัก (ตรวจกับรางวัลหน้า/ท้าย 3 ตัว)",
        "method": (
            "วิธีการคำนวณ:\n"
            "1. เอาเลขอ้างอิงมากลับหลัง\n"
            "2. นำเลขเดิมกับเลขกลับมาบวกกัน\n"
            "3. นำเลขเดิมกับเลขกลับมาลบกัน\n"
            "4. นำเลขเดิมคูณ 2"
        ),
        "input_spec": REFERENCE_INPUT_SPEC,
        "output_spec": THREE_NUMBERS_OUTPUT_SPEC,
    },
    {
        "code": "even_odd",
        "version": "1.0",
        "name": "สูตรเลขคู่คี่",
        "description": "สูตรคำนวณโดยแยกเลขคู่และเลขคี่ ผลลัพธ์เป็นเลข 3 หลัก (ตรวจกับรางวัลหน้า/ท้าย 3 ตัว)",
        "method": (
            "วิธีการคำนวณ:\n"
            "1. แยกเลขคู่และเลขคี่จากเลขอ้างอิง\n"
            "2. รวมเลขคู่ทั้งหมด\n"
            "3. รวมเลขคี่ทั้งหมด\n"
            "4. นำผลรวมมาคำนวณต่อ"
        ),
        "input_spec": REFERENCE_INPUT_SPEC,
        "output_spec": THREE_NUMBERS_OUTPUT_SPEC,
    },
]


class Command(BaseCommand):
    help = "Seed สูตรคำนวณที่อนุมัติแบบ idempotent (ไม่สร้างผลหวย/ผลวัดปลอม)"

    def handle(self, *args, **options):
        for entry in FORMULA_REGISTRY:
            # แยก create/update: สร้างใหม่ตั้งผลวัด 0/0, รันซ้ำอัปเดตแค่ contract
            # (ผลวัดจริงของ Task 15 ต้องไม่ถูกล้าง)
            formula, created = LotteryFormula.objects.get_or_create(
                code=entry["code"],
                defaults={
                    "version": entry["version"],
                    "name": entry["name"],
                    "description": entry["description"],
                    "method": entry["method"],
                    "input_spec": entry["input_spec"],
                    "output_spec": entry["output_spec"],
                    "is_approved": True,
                    "accuracy_rate": 0,
                    "total_predictions": 0,
                    "correct_predictions": 0,
                },
            )
            if not created:
                formula.version = entry["version"]
                formula.name = entry["name"]
                formula.description = entry["description"]
                formula.method = entry["method"]
                formula.input_spec = entry["input_spec"]
                formula.output_spec = entry["output_spec"]
                formula.is_approved = True
                formula.save(update_fields=[
                    "version", "name", "description", "method",
                    "input_spec", "output_spec", "is_approved",
                ])
            action = "สร้าง" if created else "อัปเดต"
            self.stdout.write(f"{action}สูตร {formula.code} v{formula.version}: {formula.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed สูตรเสร็จสิ้น: {LotteryFormula.objects.filter(is_approved=True).count()} สูตร"
            )
        )
