from django.db import models
from django.utils import timezone


class JobRun(models.Model):
    """สถานะงานตามตาราง (Task 24) — แถวละ 1 job key, เป็น lock กันรันทับด้วย."""

    STATUS_CHOICES = [
        ("idle", "ยังไม่เคยรัน"),
        ("running", "กำลังรัน"),
        ("success", "สำเร็จ"),
        ("failed", "ล้มเหลว"),
        ("skipped", "ข้าม"),
    ]

    key = models.SlugField("รหัสงาน", max_length=50, unique=True)
    title = models.CharField("ชื่องาน", max_length=200, blank=True)
    owner = models.CharField("ผู้รับผิดชอบ", max_length=100, blank=True)
    status = models.CharField(
        "สถานะล่าสุด", max_length=10, choices=STATUS_CHOICES, default="idle"
    )
    last_run_at = models.DateTimeField("รันล่าสุด", null=True, blank=True)
    last_success_at = models.DateTimeField("สำเร็จล่าสุด", null=True, blank=True)
    last_error = models.TextField("ข้อผิดพลาดล่าสุด", blank=True, default="")
    consecutive_failures = models.IntegerField("ล้มเหลวติดกัน", default=0)
    attempts_left = models.IntegerField("ครั้งลองซ้ำที่เหลือ", default=0)
    next_run_at = models.DateTimeField(
        "รอบถัดไป", null=True, blank=True,
        help_text="None = ถึงกำหนดทันที",
    )
    locked_at = models.DateTimeField("ล็อกเมื่อ", null=True, blank=True)
    last_duration_seconds = models.FloatField("ใช้เวลารอบล่าสุด (วินาที)", null=True, blank=True)

    class Meta:
        verbose_name = "งานตามตาราง"
        verbose_name_plural = "งานตามตาราง"

    def __str__(self):
        return f"{self.key} ({self.get_status_display()})"

    def is_fresh(self, threshold_hours, now=None):
        """True = เคยสำเร็จและยังไม่เกิน threshold."""
        if not self.last_success_at:
            return False
        now = now or timezone.now()
        age = (now - self.last_success_at).total_seconds() / 3600
        return age <= threshold_hours
