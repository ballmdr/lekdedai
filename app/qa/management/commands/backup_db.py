"""Task 25: backup ฐานข้อมูลอัตโนมัติ (เรียกจาก cron รายวัน)."""
from django.core.management.base import BaseCommand, CommandError

from qa.backup import backup_dir, backup_sqlite, is_sqlite


class Command(BaseCommand):
    help = "Backup ฐานข้อมูล (SQLite เต็มรูปแบบ; Postgres ต้องมี pg_dump)"

    def add_arguments(self, parser):
        parser.add_argument("--keep", type=int, default=7)

    def handle(self, *args, **options):
        if not is_sqlite():
            return self._backup_postgres(options["keep"])
        dest = backup_sqlite(keep=options["keep"])
        self.stdout.write(self.style.SUCCESS(f"Backup แล้ว: {dest}"))

    def _backup_postgres(self, keep):
        import shutil
        import subprocess
        from datetime import datetime

        if shutil.which("pg_dump") is None:
            raise CommandError("ไม่พบ pg_dump บนเครื่องนี้")
        dest_dir = backup_dir()
        dest = dest_dir / (
            f"lekdedai-{datetime.now().strftime('%Y%m%d-%H%M%S')}.sql.gz"
        )
        proc = subprocess.run(
            ["sh", "-c", f"pg_dump \"$DATABASE_URL\" | gzip > \"{dest}\""],
            capture_output=True,
            text=True,
            timeout=1800,
        )
        if proc.returncode != 0:
            raise CommandError(f"pg_dump ล้มเหลว: {proc.stderr[-500:]}")
        self.stdout.write(self.style.SUCCESS(f"Backup แล้ว: {dest}"))
