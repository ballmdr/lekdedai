from django.core.management.base import BaseCommand

from ai_engine.models import DataSource
from news.ingestion import ingest_source


class Command(BaseCommand):
    help = "ดึงข่าวจาก RSS feed ของ DataSource ที่อนุมัติ (เส้นทางหลัก Task 17)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="จำนวนข่าวต่อ feed ที่จะดึง (default: 20)",
        )
        parser.add_argument(
            "--source",
            type=str,
            help="ดึงเฉพาะแหล่งเดียว (ระบุ key หรือชื่อ)",
        )
        parser.add_argument(
            "--analyze",
            action="store_true",
            help="ลองวิเคราะห์ด้วย AI ภายนอกแบบ best-effort (ล้มเหลวได้ ข้อมูลไม่หาย)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="ดึงและประเมินเท่านั้น ไม่เขียนฐานข้อมูล",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        source_key = options.get("source")
        use_ai = options["analyze"]
        dry_run = options["dry_run"]

        if source_key:
            sources = DataSource.objects.filter(key=source_key)
            if not sources.exists():
                sources = DataSource.objects.filter(
                    name__icontains=source_key, is_active=True
                )
        else:
            sources = DataSource.objects.filter(
                source_type="news", category="rss", is_active=True
            )

        if not sources.exists():
            self.stdout.write(self.style.WARNING("No active RSS feeds found"))
            return

        analyzer = None
        if use_ai:
            from news.analyzer_switcher import AnalyzerSwitcher

            analyzer = AnalyzerSwitcher()

        totals = {"created": 0, "published": 0, "drafts": 0, "duplicates": 0}
        for source in sources:
            self.stdout.write(f"ดึงข่าวจาก: {source.name}")
            summary = ingest_source(
                source, limit=limit, analyzer=analyzer, dry_run=dry_run
            )
            if not summary["ok"]:
                self.stdout.write(self.style.ERROR(f"ล้มเหลว: {summary['error']}"))
                continue
            made = summary["would_create"] if dry_run else summary["created"]
            self.stdout.write(
                f"OK {source.name}: ตรวจ {summary['examined']} ข่าว, "
                f"{'จะสร้าง' if dry_run else 'สร้าง'} {made} "
                f"(เผยแพร่ {summary['published']}, ร่าง {summary['drafts']}, "
                f"ซ้ำ {summary['duplicates']}, AI ล้มเหลว {summary['analysis_failed']})"
            )
            totals["created"] += made
            totals["published"] += summary["published"]
            totals["drafts"] += summary["drafts"]
            totals["duplicates"] += summary["duplicates"]

        self.stdout.write("=" * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f"เสร็จสิ้น (dry_run={dry_run}): สร้าง {totals['created']} ข่าว "
                f"(เผยแพร่ {totals['published']}, ร่าง {totals['drafts']}, ซ้ำ {totals['duplicates']})"
            )
        )
