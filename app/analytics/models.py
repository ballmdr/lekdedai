"""Task 28: analytics ขั้นต่ำแบบรักษาความเป็นส่วนตัว.

เก็บเฉพาะชื่อ event + session id แบบสุ่ม (ไม่ผูกตัวตน) + เวลา + งวด
ห้ามเก็บข้อความฝัน เลขที่บันทึก IP ชื่อ หรือ free text ใด ๆ.
"""
from django.db import models
from django.utils import timezone


class AnalyticsEvent(models.Model):
    EVENT_CHOICES = [
        ("landing_view", "เปิดหน้าแรก"),
        ("dream_started", "เริ่มวิเคราะห์ฝัน"),
        ("dream_completed", "วิเคราะห์ฝันสำเร็จ"),
        ("formula_used", "ใช้เครื่องคำนวณสูตร"),
        ("news_opened", "เปิดอ่านข่าว"),
        ("number_saved", "บันทึกเลขลงสมุด"),
        ("result_checked", "ตรวจผลหวย"),
        ("history_viewed", "ดูประวัติ"),
        ("share_used", "แชร์/คัดลอก"),
    ]

    name = models.CharField("event", max_length=32, choices=EVENT_CHOICES, db_index=True)
    session_id = models.CharField("รหัสเซสชัน (สุ่ม ไม่ผูกตัวตน)", max_length=32, db_index=True)
    draw_period = models.DateField("งวดที่ event อยู่ในช่วง", null=True, blank=True, db_index=True)
    created_at = models.DateTimeField("เวลา", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "event analytics"
        verbose_name_plural = "event analytics"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["name", "created_at"])]

    def __str__(self):
        return f"{self.name} ({self.created_at:%d/%m %H:%M})"

    def save(self, *args, **kwargs):
        # Task 28: ห้ามมี payload อื่นหลุดเข้ามา — เก็บเฉพาะฟิลด์ที่ประกาศ
        self.session_id = (self.session_id or "")[:32]
        if not self.draw_period:
            self.draw_period = compute_draw_period(timezone.now().date())
        super().save(*args, **kwargs)


def compute_draw_period(on_date, upcoming=None):
    """งวดที่ date นี้อยู่ในช่วง: งวดถัดไปนับจากวันนั้น (วันหวยออกถือนับงวดนั้น)."""
    from utils.lottery_dates import LotteryDates

    if upcoming is None:
        upcoming = LotteryDates.get_upcoming_draw_dates(1, reference_date=on_date)
    if not upcoming:
        return None
    from datetime import datetime

    return datetime.strptime(upcoming[0], "%Y-%m-%d").date()
