from django.core.management.base import BaseCommand

from lotto_formula.verification import verify_pending_predictions


class Command(BaseCommand):
    help = "ตรวจผลทำนายของสูตรที่ค้างกับผลหวยจริง (เฉพาะงวดที่ผ่านไปแล้ว)"

    def handle(self, *args, **options):
        summary = verify_pending_predictions()
        self.stdout.write(
            f"ตรวจแล้ว {summary['checked']} แถว: "
            f"ถูก {summary['won']}, ไม่ถูก {summary['lost']}, "
            f"ข้าม (ยังไม่มีผล) {summary['skipped_no_result']}"
        )
        self.stdout.write(self.style.SUCCESS("ตรวจผลย้อนหลังเสร็จสิ้น"))
