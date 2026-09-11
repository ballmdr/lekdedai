"""Task 30 QA: ซ่อนข่าวที่เผยแพร่แต่ยังไม่ผ่านการวิเคราะห์ (analysis_status != analyzed).

ใช้หลังเปลี่ยนนโยบาย: ข่าวที่ถูก auto-publish ก่อนหน้านี้อาจมีเลขจาก regex ที่ยัง
ไม่ตรวจ ควรถูก demote กลับเป็น draft เพื่อให้ staff ตรวจ/อนุมัติก่อนเผยแพร่.

ค่าเริ่มต้น dry-run — ต้องใส่ --confirm จึงแก้จริง.
"""
from django.core.management.base import BaseCommand

from news.models import NewsArticle


class Command(BaseCommand):
    help = "demote ข่าว published ที่ analysis_status != analyzed กลับเป็น draft"

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true", help="แก้ข้อมูลจริง")

    def handle(self, *args, **options):
        qs = NewsArticle.objects.filter(status="published").exclude(
            analysis_status="analyzed"
        )
        count = qs.count()
        self.stdout.write(
            f"พบข่าว published ที่ยังไม่วิเคราะห์: {count} รายการ"
        )
        if not options["confirm"]:
            self.stdout.write(
                self.style.WARNING("dry-run — ใส่ --confirm เพื่อ demote จริง")
            )
            return
        updated = qs.update(status="draft")
        self.stdout.write(self.style.SUCCESS(f"demote แล้ว {updated} รายการ"))
