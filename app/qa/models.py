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


class BetaInvite(models.Model):
    """Task 30: รหัสเชิญเข้า closed beta — ใช้ tracking ว่าใครใช้ไปกี่ครั้ง."""

    code = models.CharField("รหัสเชิญ", max_length=64, unique=True)
    label = models.CharField("หมายเหตุ/กลุ่มผู้ใช้", max_length=120, blank=True)
    max_uses = models.PositiveIntegerField(
        "จำนวนใช้สูงสุด", default=0, help_text="0 = ไม่จำกัด"
    )
    used_count = models.PositiveIntegerField("ใช้ไปแล้ว", default=0)
    is_active = models.BooleanField("เปิดใช้", default=True)
    created_at = models.DateTimeField("สร้างเมื่อ", auto_now_add=True)
    last_used_at = models.DateTimeField("ใช้ล่าสุด", null=True, blank=True)

    class Meta:
        verbose_name = "รหัสเชิญ beta"
        verbose_name_plural = "รหัสเชิญ beta"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} ({self.used_count}/{self.max_uses or '∞'})"

    def has_capacity(self):
        return self.max_uses == 0 or self.used_count < self.max_uses

    def redeem(self, now=None):
        """ใช้รหัสได้สำเร็จหรือไม่ (atomic กันใช้เกินโควตาพร้อมกัน)."""
        from django.db import transaction
        from django.db.models import F

        now = now or timezone.now()
        with transaction.atomic():
            row = (
                BetaInvite.objects.select_for_update()
                .filter(pk=self.pk, is_active=True)
                .first()
            )
            if row is None or not row.has_capacity():
                return False
            BetaInvite.objects.filter(pk=row.pk).update(
                used_count=F("used_count") + 1, last_used_at=now
            )
        self.refresh_from_db()
        return True


class SystemFlag(models.Model):
    """Task 30: ธงเหตุการณ์ (เช่น P0 ผลหวยผิด) — staff เปิด/ปิดใน admin.

    flag P0 ที่ยัง active จะทำให้ beta เข้าสถานะ closed อัตโนมัติ (หยุดรับคน).
    """

    LEVEL_CHOICES = [
        ("P0", "P0 — หยุด rollout ทันที"),
        ("P1", "P1 — เฝ้าระวัง"),
        ("P2", "P2 — บันทึกไว้"),
    ]

    key = models.SlugField("รหัสเหตุการณ์", max_length=50, unique=True)
    level = models.CharField("ระดับ", max_length=2, choices=LEVEL_CHOICES, default="P1")
    message = models.CharField("ข้อความประกาศ", max_length=300)
    is_active = models.BooleanField("ยังไม่ปิดเหตุ", default=True)
    created_at = models.DateTimeField("เปิดเมื่อ", auto_now_add=True)
    resolved_at = models.DateTimeField("ปิดเมื่อ", null=True, blank=True)

    class Meta:
        verbose_name = "ธงเหตุการณ์"
        verbose_name_plural = "ธงเหตุการณ์"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.level}] {self.key} ({'active' if self.is_active else 'closed'})"
