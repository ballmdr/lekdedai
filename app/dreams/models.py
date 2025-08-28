from django.db import models
from django.contrib.auth.models import User

class DreamCategory(models.Model):
    """หมวดหมู่ความฝัน"""
    name = models.CharField("ชื่อหมวดหมู่", max_length=100)
    description = models.TextField("คำอธิบาย", blank=True)
    
    class Meta:
        verbose_name = "หมวดหมู่ความฝัน"
        verbose_name_plural = "หมวดหมู่ความฝัน"
    
    def __str__(self):
        return self.name

class DreamKeyword(models.Model):
    """คำสำคัญในความฝันและเลขที่เกี่ยวข้อง"""
    keyword = models.CharField("คำสำคัญ", max_length=100, db_index=True)
    category = models.ForeignKey(
        DreamCategory,
        on_delete=models.CASCADE,
        related_name='keywords',
        verbose_name="หมวดหมู่"
    )
    
    # เลขเด่น และเลขรอง
    main_number = models.CharField("เลขเด่น", max_length=1, help_text="เลขหลักเดียว 0-9")
    secondary_number = models.CharField("เลขรอง", max_length=1, help_text="เลขหลักเดียว 0-9")
    
    # เลขที่มักตี (combinations)
    common_numbers = models.CharField(
        "เลขที่มักตี", 
        max_length=100,
        help_text="ใส่เลขคั่นด้วยเครื่องหมายจุลภาค เช่น 12,34,56"
    )
    
    # เก็บ numbers แบบเดิมไว้เพื่อ backward compatibility
    numbers = models.CharField(
        "เลขที่เกี่ยวข้อง", 
        max_length=100,
        blank=True,
        help_text="จะถูกสร้างอัตโนมัติจาก common_numbers"
    )
    
    class Meta:
        verbose_name = "คำสำคัญความฝัน"
        verbose_name_plural = "คำสำคัญความฝัน"
        ordering = ['keyword']
    
    def save(self, *args, **kwargs):
        """อัปเดต numbers field อัตโนมัติจาก common_numbers"""
        if self.common_numbers:
            self.numbers = self.common_numbers
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.keyword} - เลขเด่น: {self.main_number}, เลขรอง: {self.secondary_number}"
    
    def get_numbers_list(self):
        """แปลงเลขเป็น list"""
        return [num.strip() for num in self.common_numbers.split(',') if num.strip()]
    
    def get_main_combinations(self):
        """สร้างเลขจากเลขเด่นและเลขรอง"""
        main = self.main_number
        secondary = self.secondary_number
        
        combinations = [
            f"{main}{secondary}",  # เลขเด่น + เลขรอง
            f"{secondary}{main}",  # เลขรอง + เลขเด่น
            f"{main}{main}",       # เลขเด่น + เลขเด่น
        ]
        
        return combinations

class DreamInterpretation(models.Model):
    """การตีความฝันของผู้ใช้"""
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ผู้ใช้"
    )
    dream_text = models.TextField("รายละเอียดความฝัน")
    interpreted_at = models.DateTimeField("วันที่ตีความ", auto_now_add=True)
    
    # ผลการตีความ
    keywords_found = models.TextField("คำสำคัญที่พบ", blank=True)
    suggested_numbers = models.CharField("เลขที่แนะนำ", max_length=200, blank=True)
    interpretation = models.TextField("คำทำนาย", blank=True)
    
    # ข้อมูลเพิ่มเติม
    ip_address = models.GenericIPAddressField("IP Address", null=True, blank=True)
    
    class Meta:
        verbose_name = "การตีความฝัน"
        verbose_name_plural = "การตีความฝัน"
        ordering = ['-interpreted_at']
    
    def __str__(self):
        return f"ความฝันเมื่อ {self.interpreted_at.strftime('%d/%m/%Y %H:%M')}"