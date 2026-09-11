"""Task 29: staging dress rehearsal — รันหนึ่งรอบงวด + fault injection.

เขียนรายงานลง reports/rehearsal-<timestamp>.json (มี sha256 + git rev)
exit code: 0 = pass/degraded, 1 = fail (ผูกกับ CI/staging gate ได้).
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from qa.rehearsal import run_rehearsal


class Command(BaseCommand):
    help = "จำลองหนึ่งรอบงวดบน staging (happy path + เหตุขัดข้อง) พร้อมรายงาน"

    def add_arguments(self, parser):
        parser.add_argument("--keep", action="store_true", help="ไม่ลบข้อมูล rehearsal")
        parser.add_argument("--report-dir", type=str, default=None)

    def handle(self, *args, **options):
        report = run_rehearsal(cleanup=not options["keep"])
        report_dir = Path(options["report_dir"]) if options["report_dir"] else (
            Path(settings.BASE_DIR).parent / "reports"
        )
        report_dir.mkdir(parents=True, exist_ok=True)
        stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
        path = report_dir / f"rehearsal-{stamp}.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        for step in report["steps"]:
            mark = {"pass": "OK", "degraded": "WARN", "fail": "FAIL", "skipped": "SKIP"}[step["status"]]
            self.stdout.write(
                f"[{mark}] {step['name']} ({step['seconds']}s) — {step['detail']}"
            )
        self.stdout.write(f"\nรายงาน: {path}")
        self.stdout.write(f"overall: {report['overall']} · sha256: {report['report_sha256'][:16]}…")

        if report["overall"] == "fail":
            raise SystemExit(1)
