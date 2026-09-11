from django.core.management.base import BaseCommand
from django.utils import timezone

from ai_engine.models import DataSource
from news.ingestion import check_source_compliance


class Command(BaseCommand):
    help = "ตรวจเงื่อนไขก่อนเปิดใช้งานแหล่งข่าว (robots + ดึงตัวอย่างได้จริง)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source", type=str, default=None,
            help="ตรวจเฉพาะแหล่งเดียว (ระบุ key หรือชื่อ)",
        )
        parser.add_argument(
            "--approve", action="store_true",
            help="อนุมัติสิทธิ์เฉพาะแหล่งที่ผ่านทุกข้อ",
        )

    def handle(self, *args, **options):
        if options["source"]:
            sources = DataSource.objects.filter(key=options["source"])
            if not sources.exists():
                sources = DataSource.objects.filter(
                    name__icontains=options["source"]
                )
        else:
            sources = DataSource.objects.filter(source_type="news").order_by("key")

        if not sources.exists():
            self.stdout.write(self.style.WARNING("ไม่พบแหล่งข่าว"))
            return

        for source in sources:
            report = check_source_compliance(source)
            mark = "OK" if report["ok"] else "FAIL"
            self.stdout.write(
                f"[{mark}] {source.key or source.name}: {report['detail']} "
                f"(สิทธิ์ปัจจุบัน: {source.get_license_status_display()})"
            )
            if options["approve"] and report["ok"]:
                source.license_status = "approved"
                source.license_note = (
                    f"ตรวจผ่าน {timezone.now():%d/%m/%Y}: {report['detail']}"
                )
                source.save(update_fields=["license_status", "license_note"])
                self.stdout.write(f"  -> อนุมัติสิทธิ์แล้ว")
