"""ซิงค์ข้อมูลหวยจาก lottery_checker (canonical LottoResult) เข้า lotto_stats.

Task 6: ใช้ LottoSyncService เป็นตัวแปลงเดียว (source of truth) เพื่อไม่ให้
ผลหน้า /lotto_stats/ กับ /lottery_checker/ ไม่ตรงกัน. Command นี้ต้องไม่
implement การแปลงข้อมูลเองซ้ำ.
"""
from django.core.management.base import BaseCommand

from lotto_stats.lotto_sync_service import LottoSyncService
from lotto_stats.models import LotteryDraw


class Command(BaseCommand):
    help = "ซิงค์ข้อมูลหวยจาก lottery_checker ไปยัง lotto_stats (ผ่าน LottoSyncService)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days-back", type=int, default=30,
            help="จำนวนวันที่ต้องการดึงข้อมูลย้อนหลัง (default: 30)",
        )
        parser.add_argument(
            "--force", action="store_true",
            help="ซิงค์ทับข้อมูลที่มีอยู่แล้ว (ค่าเริ่มต้นก็ reconcile จาก canonical อยู่แล้ว)",
        )
        parser.add_argument(
            "--clear-existing", action="store_true",
            help="ล้างข้อมูลเดิมใน lotto_stats ก่อนซิงค์",
        )

    def handle(self, *args, **options):
        days_back = options["days_back"]
        force = options["force"]
        clear_existing = options["clear_existing"]

        if clear_existing:
            self.stdout.write("ล้างข้อมูลทั้งหมดใน lotto_stats...")
            LotteryDraw.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("ล้างข้อมูลเสร็จสิ้น"))

        self.stdout.write("เริ่มซิงค์ข้อมูลหวยตามวันที่ออกที่กำหนด...")

        result = LottoSyncService().sync_recent_data(days_back, force)

        if not isinstance(result, dict) or not result.get("success"):
            self.stdout.write(
                self.style.ERROR(f"ซิงค์ไม่สำเร็จ: {result.get('error') if isinstance(result, dict) else result}")
            )
            return

        for line in result.get("results", []):
            self.stdout.write(line)

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("สรุปการซิงค์ข้อมูล")
        self.stdout.write("=" * 50)
        self.stdout.write(f"สำเร็จ: {result.get('synced_count', 0)} รายการ")
        self.stdout.write(f"ล้มเหลว: {result.get('error_count', 0)} รายการ")
        self.stdout.write(f"รวมวันที่ทั้งหมด: {result.get('total_dates', 0)}")

        if result.get("error_count", 0) == 0:
            self.stdout.write(self.style.SUCCESS("ซิงค์ข้อมูลสำเร็จ!"))
        else:
            self.stdout.write(self.style.WARNING("ซิงค์ข้อมูลเสร็จสิ้น แต่มีข้อผิดพลาดบางส่วน"))
