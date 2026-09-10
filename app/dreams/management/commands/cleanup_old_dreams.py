"""Task 7: retention ข้อความฝัน — ลบแถวเกินกำหนด + ล้าง IP เก่าที่เคยเก็บ."""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from dreams.models import DreamInterpretation


class Command(BaseCommand):
    help = "ลบประวัติฝันเกิน retention และล้าง IP เก่า (default 90 วัน)"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=90)

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)

        deleted, _ = DreamInterpretation.objects.filter(
            interpreted_at__lt=cutoff
        ).delete()
        nulled = DreamInterpretation.objects.exclude(ip_address__isnull=True).update(
            ip_address=None
        )
        self.stdout.write(
            self.style.SUCCESS(f"ลบ {deleted} แถวเกิน {days} วัน, ล้าง IP {nulled} แถว")
        )
