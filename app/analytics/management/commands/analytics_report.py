"""Task 28/30: รายงาน analytics รายงวด — activation, completion, result-check, retention.

บันทึกเป็นไฟล์ได้ด้วย `--output <path>` (และ `--format json` สำหรับเครื่องอ่าน).
"""
import json as json_module
from pathlib import Path

from django.core.management.base import BaseCommand

from analytics.report import build_report, format_text


class Command(BaseCommand):
    help = "รายงาน funnel/activation/retention จาก analytics (ไม่รวมข้อความฝัน/เลข/IP)"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)
        parser.add_argument(
            "--output", type=str, default="",
            help="เขียนรายงานลงไฟล์ (ไม่ระบุ = พิมพ์ออก stdout)",
        )
        parser.add_argument(
            "--format", choices=["text", "json"], default="text",
            help="รูปแบบไฟล์เมื่อใช้ --output",
        )

    def handle(self, *args, **options):
        report = build_report(days=options["days"])

        if options["output"]:
            path = Path(options["output"])
            path.parent.mkdir(parents=True, exist_ok=True)
            if options["format"] == "json":
                path.write_text(
                    json_module.dumps(report, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            else:
                path.write_text(format_text(report), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"เขียนรายงานแล้ว: {path}"))
            return

        self.stdout.write(format_text(report))
