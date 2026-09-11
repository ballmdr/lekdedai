from django.db import models

class HomePage(models.Model):
    title = models.CharField(max_length=255, default="LekDedAI")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    """ข้อความติดต่อ/แจ้งปัญหา/ขอลบข้อมูล (Task 26) — แอดมินจัดการใน admin."""

    TYPE_CHOICES = [
        ("contact", "ติดต่อทั่วไป"),
        ("report", "แจ้งเนื้อหาไม่เหมาะสม"),
        ("removal", "ขอลบข้อมูล"),
    ]
    STATUS_CHOICES = [
        ("new", "ใหม่"),
        ("read", "อ่านแล้ว"),
        ("done", "ดำเนินการแล้ว"),
    ]

    message_type = models.CharField("ประเภท", max_length=10, choices=TYPE_CHOICES, default="contact")
    name = models.CharField("ชื่อ", max_length=100, blank=True)
    contact = models.CharField("ช่องทางติดต่อกลับ", max_length=254, blank=True)
    message = models.TextField("ข้อความ")
    status = models.CharField("สถานะ", max_length=10, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField("ส่งเมื่อ", auto_now_add=True)

    class Meta:
        verbose_name = "ข้อความติดต่อ"
        verbose_name_plural = "ข้อความติดต่อ"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_message_type_display()} จาก {self.name or 'ไม่ระบุชื่อ'} ({self.created_at:%d/%m/%Y})"