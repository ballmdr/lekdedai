"""Task 30: สร้างรหัสเชิญ beta จาก settings.BETA_INVITE_CODES แบบ idempotent.

ตัวอย่าง:
    BETA_INVITE_CODES=code-a,code-b python app/manage.py seed_beta_invites --label "รอบแรก"
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from qa.models import BetaInvite


class Command(BaseCommand):
    help = "seed รหัสเชิญ beta จาก env BETA_INVITE_CODES (รันซ้ำได้ ไม่สร้างซ้ำ)"

    def add_arguments(self, parser):
        parser.add_argument("--label", type=str, default="env")
        parser.add_argument(
            "--max-uses", type=int, default=0, help="0 = ไม่จำกัด"
        )

    def handle(self, *args, **options):
        codes = [str(c).strip() for c in getattr(settings, "BETA_INVITE_CODES", []) if c.strip()]
        if not codes:
            self.stdout.write(self.style.WARNING("ไม่มี BETA_INVITE_CODES ใน env"))
            return
        created = 0
        for code in codes:
            _, was_created = BetaInvite.objects.get_or_create(
                code=code,
                defaults={
                    "label": options["label"],
                    "max_uses": options["max_uses"],
                },
            )
            created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(
                f"ตรวจ {len(codes)} รหัส — สร้างใหม่ {created}, มีอยู่แล้ว {len(codes) - created}"
            )
        )
