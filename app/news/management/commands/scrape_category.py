from django.core.management.base import BaseCommand

from ai_engine.models import DataSource
from news.category_scraper import rss_has_fresh_data, scrape_category_source


class Command(BaseCommand):
    help = "ขูดหน้าหมวดหมู่ข่าว (fallback ใช้เฉพาะเมื่อ RSS ไม่มีข้อมูล) เข้า review queue"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="จำนวนข่าวต่อแหล่งที่จะดึง (default: 5)",
        )
        parser.add_argument(
            "--source",
            type=str,
            help="ดึงเฉพาะแหล่งเดียว (ระบุ key หรือชื่อ)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="ดึงและประเมินเท่านั้น ไม่เขียนฐานข้อมูล",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="บังคับรันแม้ RSS จะมีข้อมูลล่าสุด",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        source_key = options.get("source")
        dry_run = options["dry_run"]

        if source_key:
            sources = DataSource.objects.filter(key=source_key)
            if not sources.exists():
                sources = DataSource.objects.filter(
                    name__icontains=source_key, category="category_page"
                )
        else:
            sources = DataSource.objects.filter(
                source_type="news", category="category_page", is_active=True
            )

        if not sources.exists():
            self.stdout.write(self.style.WARNING("No active category sources found"))
            return

        if not options["force"] and rss_has_fresh_data():
            self.stdout.write(
                "RSS มีข้อมูลในช่วง 24 ชม. ล่าสุด — ข้าม fallback (ใช้ --force เพื่อบังคับ)"
            )
            return

        for source in sources:
            self.stdout.write(f"ขูดข่าวจาก: {source.name}")
            summary = scrape_category_source(source, limit=limit, dry_run=dry_run)
            if not summary["ok"]:
                self.stdout.write(self.style.ERROR(f"ล้มเหลว: {summary['error']}"))
                continue
            made = summary["would_create"] if dry_run else summary["created"]
            self.stdout.write(
                f"OK {source.name}: ตรวจ {summary['examined']} ข่าว, "
                f"{'จะสร้าง' if dry_run else 'สร้างร่าง'} {made} "
                f"(ซ้ำ {summary['duplicates']}, ข้าม {summary['skipped']}) — "
                f"รอตรวจใน admin ก่อนเผยแพร่"
            )
