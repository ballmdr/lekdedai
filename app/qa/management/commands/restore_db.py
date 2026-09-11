"""Task 25: คืนฐานข้อมูลจากไฟล์ backup (อันตราย — ต้อง --confirm).

ขั้นตอนปลอดภัยอยู่ใน docs/OPERATIONS.md (หยุด web ก่อนเสมอ).
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from qa.backup import is_sqlite, restore_sqlite


class Command(BaseCommand):
    help = "คืนฐานข้อมูล SQLite จากไฟล์ .gz (ต้องหยุด web ก่อน + --confirm)"

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True)
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="ยืนยันว่าหยุด web แล้วและยอมทับฐานข้อมูลปัจจุบัน",
        )

    def handle(self, *args, **options):
        if not is_sqlite():
            raise CommandError(
                "คำสั่งนี้รองรับเฉพาะ SQLite (Postgres ให้คืนด้วย pg_restore ตาม runbook)"
            )
        if not options["confirm"]:
            raise CommandError("ต้องหยุด web ก่อน แล้วรันพร้อม --confirm")
        backup_file = Path(options["file"])
        if not backup_file.exists():
            raise CommandError(f"ไม่พบไฟล์: {backup_file}")
        tables = restore_sqlite(backup_file)
        if not tables:
            raise CommandError("ไฟล์ backup เสีย (ไม่พบตาราง)")
        self.stdout.write(
            self.style.SUCCESS(f"คืนฐานข้อมูลแล้ว ({tables} ตาราง) — สตาร์ท web ใหม่ได้")
        )
